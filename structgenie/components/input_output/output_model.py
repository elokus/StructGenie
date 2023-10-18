from typing import Type

from pydantic import BaseModel, Field

from structgenie.base import BaseExample
from structgenie.components.input_output._example_parser import type_schema_from_examples
from structgenie.components.input_output._extract_notation import io_lines_from_string
from structgenie.components.input_output._pydantic_parser import extract_model
from structgenie.components.input_output.base import IOModel
from structgenie.components.input_output.line import IOLine

T = Type[BaseModel]


class OutputModel(IOModel):
    lines: list[IOLine] = Field(default_factory=lambda: [IOLine(key="output", type="str")])

    # === class methods ===

    @classmethod
    def from_string(cls, string: str):
        attributes = io_lines_from_string(string)
        return cls(lines=[IOLine(**attr) for attr in attributes])

    @classmethod
    def from_examples(cls, examples: list[BaseExample], **kwargs):
        type_schema = type_schema_from_examples(examples, target="output", **kwargs)
        return cls.from_dict(type_schema)

    @classmethod
    def from_pydantic(cls, pydantic_model: T):
        return cls(lines=extract_model(pydantic_model))

    # === properties ===

    @property
    def prompt_schema(self) -> str:
        return "\n".join([attribute.to_prompt_output_legacy() for attribute in self.lines])

    @property
    def template_schema(self) -> str:
        return "\n".join([attribute.to_type_notation() for attribute in self.lines])

    def dump_to_prompt(self, param):
        return NotImplemented
