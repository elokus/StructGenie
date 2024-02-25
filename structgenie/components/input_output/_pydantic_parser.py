from typing import Type

from pydantic import BaseModel

from structgenie.components.input_output.line import IOLine
from structgenie.utils.parsing import parse_type_from_string

NESTING_IDENTIFIERS = ["properties", "items", "additionalProperties"]
PASSING_KEYS = ["default", "rule", "placeholder", "enum", "multiple_select", "custom_value_template"]

T = Type[BaseModel]


def extract_model(model: T):
    schema = model.schema()
    properties = schema.get("properties", {})
    definitions = schema.get("definitions", None)
    if definitions is None:
        definitions = schema.get("$defs", {})

    lines = []

    for key_, value_ in properties.items():
        lines.extend(_extract_property(key_, value_, definitions))

    return lines


def extract_nested(parent_properties: dict, definitions: dict, prefix_key: str = None, prefix_type: str = None):
    lines = []
    nested_identifier = nested_key(parent_properties)

    # new line identifier
    if nested_identifier == "properties":

        lines.append(parse_line(prefix_key, parent_properties, prefix_type))

        if has_iterator_key(parent_properties):
            prefix_key = prefix_key + "." + get_iterator(parent_properties)

        lines.extend(extract_properties(parent_properties["properties"], definitions, prefix_key))
        return lines

    if has_iterator_key(parent_properties):
        lines.append(parse_line(prefix_key, parent_properties, prefix_type))
        prefix_key = prefix_key + "." + get_iterator(parent_properties)
        prefix_type = None
        lines.extend(_extract_property(prefix_key, parse_ref(parent_properties[nested_identifier], definitions),
                                       prefix_type=prefix_type))
        return lines

    # same line identifier
    if prefix_type is None:
        prefix_type = parse_type_from_string(parent_properties.get("type"))

    child_props = pass_props_to_child(parent_properties, parse_ref(parent_properties[nested_identifier], definitions))
    lines.extend(_extract_property(prefix_key, child_props, definitions, prefix_type=prefix_type))
    return lines


def parse_ref(value: dict, definitions: dict):
    if "$ref" in value:
        return definitions[value["$ref"].split('/')[-1]]
    return value


def extract_properties(properties: dict, definitions: dict = None, prefix_key: str = None):
    lines = []
    for key_, value_ in properties.items():
        lines.extend(_extract_property(key_, value_, definitions, prefix_key))
    return lines


def _extract_property(key: str, value: dict, definitions: dict = None, prefix_key: str = None, prefix_type: str = None):
    value = parse_ref(value, definitions)
    _key = f"${key}" if is_iterator_key(value) else key
    key = prefix_key + "." + _key if prefix_key is not None else _key
    if is_nested(value):
        return extract_nested(value, definitions, prefix_key=key, prefix_type=prefix_type)
    return [parse_line(key, value, prefix_type=prefix_type)]


# Helpers ---------------------------------------------------------------------

def is_iterator_key(value: dict) -> bool:
    return value.get("is_iterator", False)


def has_iterator(value: dict):
    return "rule" in value and "$" in value["rule"]


def has_iterator_key(value: dict):
    if has_iterator(value):
        return "additionalProperties" in value
    return False


def get_iterator(value: dict):
    if has_iterator(value):
        return "$" + value["rule"].split("$")[1].split(" ")[0]
    else:
        return None


def parse_line(key: str, value: dict, prefix_type: str = None):
    attributes = value.copy()
    if prefix_type is not None:
        attributes["type"] = concat_type(value, prefix_type)

    if attributes.get("enum"):
        if attributes.get("type").startswith("list"):
            attributes["multiple_select"] = True

    return IOLine(key=key, **attributes)


def concat_type(value: dict, prefix_type: str):
    if prefix_type is not None:
        if not value.get("type") and "enum" in value:
            value["type"] = str(type(value["enum"][0]).__name__)
            if None in value["enum"]:
                value["type"] = f"Union[{value['type']}, None]"
        return f"{prefix_type}[{parse_type_from_string(value['type'])}]"
    return value.get("type")


def nested_key(value: dict):
    for identifier in NESTING_IDENTIFIERS:
        if identifier in value:
            return identifier
    return None


def is_nested(value: dict):
    return nested_key(value) is not None


def pass_props_to_child(parent_props: dict, child_props: dict):
    child_props.update({key: value for key, value in parent_props.items() if key in PASSING_KEYS})
    return child_props
