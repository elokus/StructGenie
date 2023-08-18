from typing import Optional, Union

from pydantic import BaseModel, validator

from structgenie.base import BaseOutputAttribute
from structgenie.parser import parse_type_from_string


class OutputAttribute(BaseOutputAttribute):
    key: str
    type: str = "any"
    rule: Optional[str] = None
    default: Union[str, int, float, bool, list, dict] = None

    # === validators ===

    @validator("type")
    def validate_type(cls, value: str) -> str:
        return parse_type_from_string(value)

    @validator("key")
    def validate_key(cls, value: str) -> str:
        return value.replace(" ", "_").lower()

    # === class methods ===

    @classmethod
    def from_kwarg(cls, key: str, value: Union[dict, str]):

        if isinstance(value, str):
            return cls(key=key, type=value)

        type_ = value["type"]

        kwargs = {}
        if "rule" in value:
            kwargs["rule"] = value["rule"]

        if "default" in value:
            kwargs["default"] = value["default"]
        return cls(key=key, type=type_, **kwargs)

    # === properties ===

    @property
    def val_dict(self):
        return self.dict(exclude={"key"})

    @property
    def prompt_syntax(self) -> str:
        if self.rule:
            return f"{self._prompt_key}: <{self.type} ({self.rule})>"
        return f"{self._prompt_key}: <{self.type}>"

    @property
    def template_syntax(self) -> str:
        if self.rule:
            return f"<'{self.key}': {self.type} ({self.rule})>"
        return f"<'{self.key}': {self.type}>"

    @property
    def _prompt_key(self) -> str:
        return self.key.replace("_", " ").capitalize()
