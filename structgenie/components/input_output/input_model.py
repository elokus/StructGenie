from typing import Type

from pydantic import BaseModel, Field

from structgenie.base import BaseExample
from structgenie.components.input_output._example_parser import type_schema_from_examples
from structgenie.components.input_output._extract_notation import io_lines_from_string
from structgenie.components.input_output._pydantic_parser import extract_model
from structgenie.components.input_output.base import IOModel
from structgenie.components.input_output.line import IOLine
from structgenie.utils.parsing import dump_to_yaml_string

T = Type[BaseModel]


class InputModel(IOModel):
    lines: list[IOLine] = Field(default_factory=lambda: [IOLine(key="input", type="str")])

    # === class methods ===

    @classmethod
    def from_string(cls, string: str):
        attributes = io_lines_from_string(string)
        return cls(lines=[IOLine(**attr) for attr in attributes])

    @classmethod
    def from_examples(cls, examples: list[BaseExample], **kwargs):
        type_schema = type_schema_from_examples(examples, target="input", **kwargs)
        return cls.from_dict(type_schema)

    @classmethod
    def from_pydantic(cls, pydantic_model: T):
        return cls(lines=extract_model(pydantic_model))

    @property
    def prompt_schema(self) -> str:
        return "\n".join([line.to_prompt_input() for line in self.lines])

    @property
    def type_notation(self) -> str:
        return "\n".join([line.to_type_notation() for line in self.lines])

    def dump_to_prompt(self, inputs: dict, **kwargs):
        input_dict = {line.key: line.prompt_value(inputs, **kwargs) for line in self.lines if not line.hidden}
        return dump_to_yaml_string(input_dict)

    # legacy
    @property
    def template_schema(self) -> str:
        return "\n".join([line.to_template_output() for line in self.lines])

    @property
    def model_type(self):
        return "input"
