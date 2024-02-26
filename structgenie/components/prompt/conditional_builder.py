
from structgenie.base import BasePromptBuilder, BaseIOModel
from structgenie.components.input_output import init_output_model, build_output_schema
from structgenie.components.prompt._templates import (
    FORMAT_INSTRUCTIONS_TEMPLATE_CONDITIONAL,
)
from structgenie.components.prompt.builder import PromptBuilder
from structgenie.utils.parsing import parse_section_placeholder, dump_to_yaml_string


class ConditionalPromptBuilder(PromptBuilder):
    """Prompt Builder class"""

    format_template: str = FORMAT_INSTRUCTIONS_TEMPLATE_CONDITIONAL

    def __init__(
            self,
            instruction: str,
            output_model: BaseIOModel = None,
            input_model: BaseIOModel = None,
            output_model_else: BaseIOModel = None,
            condition: str = None,
            **kwargs):
        """Prompt Builder constructor"""

        self.output_model_else: BaseIOModel = init_output_model(output_model_else, **kwargs)
        self.condition: str = condition
        super().__init__(instruction, output_model, input_model, **kwargs)

    def _prep_format_instructions(self, template: str, **kwargs):
        """Prepare format instructions"""
        format_instructions = self._pass_placeholder(
            self.format_template,
            condition=self.condition,
            response_schema=dump_to_yaml_string(build_output_schema(self.output_model, inputs=kwargs)),
            response_schema_else=dump_to_yaml_string(build_output_schema(self.output_model_else, inputs=kwargs))
        )

        return parse_section_placeholder(
            template,
            set_tags=self._set_format_tags,
            format_instructions=format_instructions
        )

    @classmethod
    def from_prompt_builder(cls, prompt_builder: PromptBuilder, condition: str, output_model_else: BaseIOModel, **kwargs):
        """Build ConditionalPromptBuilder from PromptBuilder"""

        _kwargs = {
            "examples": prompt_builder.examples,
            "remarks": prompt_builder.remarks,
            "set_format_tags": prompt_builder._set_format_tags,
            "set_example_tags": prompt_builder._set_example_tags,
            "set_remarks_tags": prompt_builder._set_remarks_tags,
            "chat_mode": prompt_builder.chat_mode
        }

        if kwargs:
            _kwargs.update(kwargs)

        return cls(
            prompt_builder.instruction,
            prompt_builder.output_model,
            prompt_builder.input_model,
            output_model_else,
            condition,
            **_kwargs
        )