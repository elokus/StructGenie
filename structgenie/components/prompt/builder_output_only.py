from typing import Union

from structgenie.base import BasePromptBuilder, BaseIOModel
from structgenie.components.examples.shuffle_selector import ExampleSelector
from structgenie.components.input_output import init_output_model, build_output_schema
from structgenie.components.prompt._templates import (
    FORMAT_INSTRUCTIONS_TEMPLATE,
    ERROR_TEMPLATE
)
from structgenie.utils.parsing import replace_placeholder, parse_section_placeholder, dump_to_yaml_string

DEFAULT_TEMPLATE = """{instruction}
{format_instructions}
{examples}
{remarks}
"""

DEFAULT_SCHEMA_TEMPLATE = """{instruction}
{examples}
{remarks}
---
{output_schema}
"""


class PromptBuilder(BasePromptBuilder):
    """Prompt Builder class"""

    prompt_template: str = DEFAULT_TEMPLATE
    schema_template: str = DEFAULT_SCHEMA_TEMPLATE
    format_template: str = FORMAT_INSTRUCTIONS_TEMPLATE
    error_template: str = ERROR_TEMPLATE

    def __init__(self, instruction: str, output_model: BaseIOModel = None, **kwargs):
        """Prompt Builder constructor"""
        self.instruction: str = instruction
        self.output_model: BaseIOModel = init_output_model(output_model, **kwargs)

        self.examples: Union[str, ExampleSelector] = kwargs.get("examples")
        self.remarks: str = kwargs.get("remarks")

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
        template = self._prep_examples(template)
        template = self._prep_remarks(template)
        template = self._pass_placeholder(template, output_schema=self.output_model.template_schema)
        return template

    def build(self, error: Exception = None, **kwargs) -> str:
        """Build prompt"""
        template = self.prompt_template
        template = self._prep_instruction(template)
        template = self._prep_examples(template)
        template = self._prep_format_instructions(template, **kwargs)
        template = self._prep_remarks(template, error)
        return template

    def fix_parsing(self, error: str, **kwargs):
        return NotImplemented

    def fix_validation(self, error: str, **kwargs):
        return NotImplemented

    def _prep_instruction(self, template: str) -> str:
        """Prepare instruction"""
        return self._pass_placeholder(template, instruction=self.instruction)

    def _prep_examples(self, template: str):
        """Prepare examples"""
        if not self.examples:
            return self._pass_placeholder(template, examples="")

        return parse_section_placeholder(template, examples=self.examples.to_prompt())

    def _prep_format_instructions(self, template: str, **kwargs):
        """Prepare format instructions"""
        format_instructions = self._pass_placeholder(
            self.format_template,
            response_schema=dump_to_yaml_string(build_output_schema(self.output_model, inputs=kwargs))
        )

        return parse_section_placeholder(template, format_instructions=format_instructions)

    def _prep_remarks(self, template: str, error: Exception = None):
        """Prepare remarks"""
        remarks = self.remarks or ""
        if error:
            remarks = self._pass_placeholder(self.error_template, error=error, remarks=remarks)
        return parse_section_placeholder(template, remarks=remarks)

    @staticmethod
    def _pass_placeholder(template: str, **kwargs):
        return replace_placeholder(template, **kwargs)

    @staticmethod
    def _pass_placeholder_section(template: str, **kwargs):
        return parse_section_placeholder(template, **kwargs)
