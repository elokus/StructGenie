from abc import abstractmethod
from enum import Enum

from structgenie.base import BaseExampleSelector, BaseIOModel
from structgenie.components.input_output.line import IOLine
from structgenie.utils.parsing.placeholder import replace_placeholder_in_dict


class IOFormatType(str, Enum):
    PROMPT_OUTPUT = "prompt_output"  # Key: <type (rule)> = default
    TEMPLATE_OUTPUT = "template_output"  # Key: <type (rule)> = default
    PROMPT_INPUT = "prompt_input"  # Key: {key}


class IOModel(BaseIOModel):
    lines: list[IOLine]

    # === class methods ===

    @classmethod
    def from_dict(cls, attr_dict: dict):
        lines = []
        for key, value in attr_dict.items():
            lines.append(IOLine.from_kwarg(key, value))
        return cls(lines=lines)

    @classmethod
    @abstractmethod
    def from_string(cls, schema: str):
        pass

    @classmethod
    @abstractmethod
    def from_examples(cls, examples: BaseExampleSelector):
        pass

    # === properties ===

    @property
    def as_dict(self):
        return {attribute.key: attribute.value for attribute in self.lines}

    def to_string(self, format_type: IOFormatType, custom_input_template: str = None):

        if format_type == IOFormatType.TEMPLATE_OUTPUT:
            return "\n".join([attribute.to_type_notation() for attribute in self.lines])

        elif format_type == IOFormatType.PROMPT_OUTPUT:
            return "\n".join([attribute.to_type_notation() for attribute in self.lines])

        elif format_type == IOFormatType.PROMPT_INPUT:
            return "\n".join([attribute.to_prompt_input() for attribute in self.lines])

        raise ValueError(f"Invalid format type: {format}")

    def keys(self) -> list[str]:
        return [attribute.key for attribute in self.lines]

    def values(self) -> list[str]:
        return [attribute.value for attribute in self.lines]

    @property
    def defaults(self):
        return {attribute.key: attribute.default for attribute in self.lines if attribute.default is not None}

    # === getters ===

    def get(self, key):
        return next((attribute for attribute in self.lines if attribute.key == key), None)

    def get_nested_dict(self, key: str, full_key: bool = True, **kwargs) -> dict:
        """Get nested attributes and replace key with value it kwargs are provided"""

        data = {
            attribute.key: attribute.value for attribute in self.lines
            if attribute.key.startswith(key)
        }

        info = data.pop(key)
        data["_info"] = {"key": key, **info}

        if kwargs:
            data = replace_placeholder_in_dict(data, **kwargs)

        if full_key:
            return data
        return {k.replace(f"{key}.", ""): v for k, v in data.items()}

    def get_nested_attr(self, key: str, exclude_parent: bool = False):
        if exclude_parent:
            return [attribute for attribute in self.lines if attribute.key.startswith(f"{key}.")]
        return [attribute for attribute in self.lines if attribute.key.startswith(key)]

    def get_default(self, key: str, **kwargs):
        attr = self.get(key)
        if attr:
            default = attr.default

            if isinstance(default, str) and default in kwargs:
                return kwargs[default]
            return default

    def parse_default(self, output: dict) -> dict:
        from structgenie.utils.operator.default import parse_default
        return parse_default(output, self)

    def __len__(self):
        return len(self.lines)
