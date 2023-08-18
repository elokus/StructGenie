from typing import Union

from structgenie.base import BaseExampleSelector
from structgenie.parser import dump_to_yaml_string


def init_input_schema(input_schema: Union[str, dict, list], examples: BaseExampleSelector = None, **kwargs) -> str:
    """Initialize the input schema."""
    if input_schema:
        if isinstance(input_schema, str):
            return input_schema
        elif isinstance(input_schema, dict):
            return dump_to_yaml_string(input_schema)
        elif isinstance(input_schema, list):
            return _input_schema_from_keys(input_schema)

    if examples:
        return _input_schema_from_keys(examples.input_keys)

    return "Input: {input}"


def load_input_schema(sections: dict, examples: BaseExampleSelector = None, **kwargs) -> str:
    """Extract the input schema from the template or BaseExampleSelector it based on the provided rules."""

    # If explicit Input Schema is provided
    if sections["input_schema"]:
        return parse_schema_from_template(sections["input_schema"])

    # If no explicit Input Schema, try to extract input keys from Examples
    if examples and len(examples) > 0:
        return _input_schema_from_keys(examples.input_keys)

    return "Input: {input}"


def parse_schema_from_template(schema: str) -> str:
    """Parse the schema from the template."""
    if schema == "{input}":
        return "{{!system: parse_as_yaml: {inputs}}}"

    return schema.replace('Input:', '').replace('Output:', '').strip()


def _input_schema_from_keys(keys: list[str]) -> str:
    """Generate the input schema from the provided keys."""
    return dump_to_yaml_string({key: "{" + key + "}" for key in keys})
