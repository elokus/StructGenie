from typing import Union

from structgenie.base import BasePromptBuilder, BaseIOModel
from structgenie.components.examples.shuffle_selector import ExampleSelector
from structgenie.components.input_output import init_input_model, init_output_model, build_output_schema
from structgenie.components.prompt._templates import (
    DEFAULT_TEMPLATE,
    DEFAULT_SCHEMA_TEMPLATE,
    FORMAT_INSTRUCTIONS_TEMPLATE,
    ERROR_TEMPLATE,
    CHAT_TEMPLATE, CHAT_TEMPLATE_ON_ERROR
)
from structgenie.utils.parsing import replace_placeholder, parse_section_placeholder, dump_to_yaml_string


class PromptBuilder(BasePromptBuilder):
    """Prompt Builder class"""

    prompt_template: str = DEFAULT_TEMPLATE
    chat_template: str = CHAT_TEMPLATE
    chat_template_on_error: str = CHAT_TEMPLATE_ON_ERROR
    schema_template: str = DEFAULT_SCHEMA_TEMPLATE
    format_template: str = FORMAT_INSTRUCTIONS_TEMPLATE
    error_template: str = ERROR_TEMPLATE

    def __init__(self, instruction: str, output_model: BaseIOModel = None, input_model: BaseIOModel = None, **kwargs):
        """Prompt Builder constructor"""
        self.instruction: str = instruction
        self.output_model: BaseIOModel = init_output_model(output_model, **kwargs)
        self.input_model: BaseIOModel = init_input_model(input_model, **kwargs)

        self.examples: Union[str, ExampleSelector] = kwargs.get("examples")
        self.remarks: str = kwargs.get("remarks")
        self._set_format_tags = kwargs.get("set_format_tags", True)
        self._set_example_tags = kwargs.get("set_example_tags", True)
        self._set_remarks_tags = kwargs.get("set_remarks_tags", True)
        self.chat_mode = kwargs.get("chat_mode", False)

        self._init_templates(**kwargs)

    def _init_templates(self, **kwargs):
        if not kwargs:
            return

        for key, value in kwargs.items():
            if key in self.__annotations__:
                setattr(self, key, value)

    @property
    def parsing_error_template(self):
        return """{instruction}"""

    @property
    def validation_error_template(self):
        return """{instruction}"""

    def build_template(self, **kwargs) -> str:
        template = self.schema_template
        template = self._prep_instruction(template)
        template = self._prep_examples(template, return_all=True)
        template = self._prep_remarks(template)
        template = self._pass_placeholder(
            template,
            input=self.input_model.prompt_schema,
            output_schema=self.output_model.template_schema,
            set_tags=True
        )
        return template

    def build(self, error: str = None, remarks: str = None, last_output: str = None, chat_mode: bool = False, **kwargs) -> str:
        """Build prompt"""
        if chat_mode:
            self.chat_mode = True

        if self.chat_mode:
            template = self.chat_template if not error else self.chat_template_on_error
        else:
            template = self.prompt_template
        template = self._prep_instruction(template)
        template = self._prep_examples(template)
        template = self._prep_format_instructions(template, **kwargs)
        template = self._prep_remarks(template, error, remarks, last_output)
        # template = self._prep_inputs(template)
        return template

    def fix_parsing(self, error: str, **kwargs):
        return NotImplemented

    def fix_validation(self, error: str, **kwargs):
        return NotImplemented

    def _prep_instruction(self, template: str) -> str:
        """Prepare instruction"""
        return self._pass_placeholder(template, instruction=self.instruction)

    def _prep_examples(self, template: str, **kwargs):
        """Prepare examples"""
        if not self.examples:
            return self._pass_placeholder(template, examples="")

        return parse_section_placeholder(
            template,
            set_tags=self._set_example_tags,
            examples=self.examples.to_prompt(**kwargs)
        )

    def _prep_format_instructions(self, template: str, **kwargs):
        """Prepare format instructions"""
        format_instructions = self._pass_placeholder(
            self.format_template,
            response_schema=dump_to_yaml_string(build_output_schema(self.output_model, inputs=kwargs))
        )

        return parse_section_placeholder(
            template,
            set_tags=self._set_format_tags,
            format_instructions=format_instructions
        )

    def _prep_remarks(self, template: str, error: str = None, remarks: str = None, last_output: str = None):
        """Prepare remarks"""
        if not remarks:
            remarks = self.remarks or ""
        if error:
            if not self.chat_mode:
                remarks = self._pass_placeholder(
                    self.error_template, error=error, last_output=last_output, remarks=remarks
                )
            else:
                return parse_section_placeholder(
                    template, set_tags=False, remarks=remarks, error=error, last_output=last_output)
        return parse_section_placeholder(template, set_tags=self._set_remarks_tags, remarks=remarks)

    @staticmethod
    def _pass_placeholder(template: str, **kwargs):
        return replace_placeholder(template, **kwargs)

    @staticmethod
    def _pass_placeholder_section(template: str, **kwargs):
        return parse_section_placeholder(template, **kwargs)
