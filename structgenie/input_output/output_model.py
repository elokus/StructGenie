from pydantic import Field

from structgenie.base import BaseExampleSelector, BaseOutputModel
from structgenie.input_output._template import (
    is_prompt_syntax,
    is_template_syntax,
    output_dict_from_template,
    output_dict_from_prompt
)

from structgenie.input_output.output_attribute import OutputAttribute
from structgenie.parser.placeholder import replace_placeholder_in_dict


class OutputModel(BaseOutputModel):
    attributes: list[OutputAttribute] = Field(default_factory=lambda: [OutputAttribute(key="output", type="str")])

    # === class methods ===

    @classmethod
    def from_dict(cls, output_dict: dict):
        attributes = []
        for key, value in output_dict.items():
            attributes.append(OutputAttribute.from_kwarg(key, value))
        return cls(attributes=attributes)

    @classmethod
    def from_schema(cls, schema: str):
        schema = schema.strip()
        if is_template_syntax(schema):
            schema = output_dict_from_template(schema)
        elif is_prompt_syntax(schema):
            schema = output_dict_from_prompt(schema)
        return cls.from_dict(schema)

    @classmethod
    def from_examples(cls, examples: BaseExampleSelector):
        return cls.from_dict(examples.output_type_dict())

    # === properties ===

    @property
    def as_dict(self):
        return {attribute.key: attribute.val_dict for attribute in self.attributes}

    @property
    def prompt_schema(self) -> str:
        return "\n".join([attribute.prompt_syntax for attribute in self.attributes])

    @property
    def template_schema(self) -> str:
        return "\n".join([attribute.template_syntax for attribute in self.attributes])

    @property
    def output_keys(self) -> list[str]:
        return [attribute.key for attribute in self.attributes]

    @property
    def defaults(self):
        return {attribute.key: attribute.default for attribute in self.attributes if attribute.default is not None}

    # === getters ===

    def get(self, key):
        return next((attribute for attribute in self.attributes if attribute.key == key), None)

    def get_nested_dict(self, key: str, full_key: bool = True, **kwargs) -> dict:
        """Get nested attributes and replace key with value it kwargs are provided"""

        data = {
            attribute.key: attribute.val_dict for attribute in self.attributes
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
            return [attribute for attribute in self.attributes if attribute.key.startswith(f"{key}.")]
        return [attribute for attribute in self.attributes if attribute.key.startswith(key)]

    def get_default(self, key: str, **kwargs):
        attr = self.get(key)
        if attr:
            default = attr.default

            if isinstance(default, str) and default in kwargs:
                return kwargs[default]
            return default
