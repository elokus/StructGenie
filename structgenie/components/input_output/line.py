from typing import Optional, Union

from structgenie.pydantic_v1 import validator, root_validator

from structgenie.base import BaseIOLine
from structgenie.utils.parsing import parse_type_from_string
from structgenie.utils.parsing.string import remove_outer_quotes

KWARGS = ["type", "rule", "default", "custom_value_template", "options", "multiple_select"]


def format_capital_key(key: str) -> str:
    return key.replace("_", " ").capitalize()


def format_variable_key(key: str) -> str:
    return key.replace(" ", "_").lower()


def remove_curly_brackets(text: str) -> str:
    return text.replace("{", "").replace("}", "")


PROMPT_INPUT_TEMPLATE = "{prompt_key}: {{{key}}}"
TYPE_NOTATION_TEMPLATE_LEGACY = "<{type} ({rule})> = {default}"
TYPE_NOTATION_TEMPLATE = "{prompt_key}: <{type}{kwargs}>"

HIDDEN_TYPES = ["image", "file"]

class IOLine(BaseIOLine):
    """Represents an input or output line in the final prompt/output."""
    key: str
    type: str = "any"
    placeholder: Optional[list[str]] = None
    options: Optional[list] = None
    rule: Optional[str] = None
    default: Union[str, int, float, bool, list, dict, None] = None
    multiple_select: bool = False
    multiline: bool = False
    custom_value_template: Optional[str] = None
    hidden: bool = False
    description: Optional[str] = None

    # === validators ===

    @root_validator(pre=True)
    def validate_placeholder(cls, values):
        if not values.get("placeholder"):
            values["placeholder"] = [format_variable_key(values["key"])]
        if isinstance(values["placeholder"], str):
            values["placeholder"] = [values["placeholder"]]
        if isinstance(values["placeholder"], list):
            values["placeholder"] = [remove_curly_brackets(v) for v in values["placeholder"]]
        if values.get("enum"):
            values["options"] = values.pop("enum")
        if values.get("key").startswith("_") or values.get("type") in HIDDEN_TYPES:
            values["hidden"] = True
        return values

    @validator("options", pre=True, always=True)
    def validate_options(cls, value: Union[list, str]) -> list:
        if isinstance(value, str):
            try:
                return eval(value)
            except:
                value = value.replace("[", "").replace("]", "")
                return [v.strip() for v in value.split(",")]
        return value

    @validator("multiple_select", pre=True, always=True)
    def validate_multiple_select(cls, value: Union[bool, str]) -> bool:
        if isinstance(value, str):
            return value.lower() in ["true", "yes", "y"]
        return value

    @validator("type")
    def validate_type(cls, value: str) -> str:
        return parse_type_from_string(value)

    @validator("rule")
    def validate_rule(cls, value: str) -> str:
        if isinstance(value, str):
            value = remove_outer_quotes(value)
            return value.replace("(", "").replace(")", "")
        return value

    @validator("key")
    def validate_key(cls, value: str) -> str:
        return value.replace(" ", "_").lower()

    # === class methods ===

    @classmethod
    def from_kwarg(cls, key: str, value: Union[dict, str]):

        if isinstance(value, str):
            return cls(key=key, type=value)

        return cls(key=key, **{k: value[k] for k in KWARGS if k in value})

    # === properties ===

    @property
    def value(self):
        return {
            k: v for k, v in self.dict(exclude={"key", "custom_value_template", "placeholder"}).items()
        }

    @property
    def prompt_key(self) -> str:
        return self.key.replace("_", " ").capitalize()

    @property
    def safe_type(self):
        return self.type.split("[")[0]

    # === getters ===

    def _kwargs_dict(self, exclude: list[str] = None) -> dict:
        exclude = exclude or []
        exclude.append("custom_value_template")
        d = {k: str(v) for k, v in self.dict(exclude=set(exclude)).items() if v is not None}
        if "prompt_key" not in exclude:
            d["prompt_key"] = self.prompt_key
        if not d.get("options"):
            d.pop("multiple_select", None)

        return d

    def _kwargs_to_string(self):
        kwargs = [f"{k}={v}" for k, v in self._kwargs_dict(["type", "key", "prompt_key", "placeholder", "hidden", "multiline"]).items()]
        if kwargs:
            return f", {', '.join(kwargs)}"
        return ""

    def _line_dict(self):
        d = self._kwargs_dict()
        d["kwargs"] = self._kwargs_to_string()
        return d

    # === String Formatting ===

    def prompt_value(self, inputs: dict, **kwargs) -> str:
        """Format the line value for the prompt from input dict"""
        if self.custom_value_template:
            return self.custom_value_template.format(**inputs)
        if len(self.placeholder) == 1:
            return inputs.get(self.placeholder[0], kwargs.get(self.placeholder[0], self.default))
        raise ValueError(f"Cannot format prompt value for placeholder: {self.placeholder}")
        #
        # return inputs.get(self.key, kwargs.get(self.key, self.default))

    def to_type_notation(self) -> str:
        return TYPE_NOTATION_TEMPLATE.format(**self._line_dict())

    def to_prompt_input(self) -> str:
        return PROMPT_INPUT_TEMPLATE.format(**self._line_dict())

    # legacy
    def to_prompt_output_legacy(self) -> str:
        if self.rule:
            return f"{self.prompt_key}: <{self.type} ({self.rule})>"
        return f"{self.prompt_key}: <{self.type}>"

    # legacy
    def to_template_output(self) -> str:
        if self.rule:
            return f"<'{self.key}': {self.type} ({self.rule})>"
        return f"<'{self.key}': {self.type}>"

    # === setters ===

    def set_options(self, options: list, select_multiple: bool = False):
        if self.rule:
            raise ValueError(f"Cannot set options for attribute with rule: {self.rule}")

        if select_multiple:
            self.rule = f"one or more of {options}"

        else:
            self.rule = f"one of {options}"
