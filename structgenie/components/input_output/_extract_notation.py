import re
from typing import Union

from structgenie.components.input_output._legacy_type_notation import extract_legacy_type_notation
from structgenie.components.input_output._notation_match import (
    is_multiline_notation,
    is_type_notation,
    is_input_notation,
    is_custom_input_notation,
    is_key_value_notation,
    is_multiline_input
)
from structgenie.utils.parsing.string import remove_outer_quotes


def io_lines_from_string(text: str):
    """Parse input and output notations from templates."""
    text = text.strip()
    lines = []
    multiline = None
    for line in text.splitlines():
        if is_multiline_notation(line):
            multiline = line
            continue
        if multiline:
            line = multiline + "\n" + line
            multiline = None
        attr = parse_line(line.strip())
        lines.append(attr)
    return lines


def parse_line(line: str):
    """Parse input and output notations from templates."""
    if is_multiline_input(line):
        return parse_input_notation(line)
    if is_type_notation(line):
        return parse_type_notation(line)
    if is_input_notation(line):
        return parse_input_notation(line)
    return None


def parse_input_notation(line: str) -> Union[dict, dict]:
    """Parse input and output notations from templates."""
    key, type_schema = line.split(":")
    key = key.strip()
    if is_key_value_notation(line):
        return parse_key_value_notation(line)
    if is_custom_input_notation(line):
        return {"key": key, **parse_custom_input_notation(line)}
    return {"key": key, "type": "any"}


# Todo: remove legacy support after testing
def parse_type_notation(line: str):
    """Parse input and output notations from templates."""
    key, type_schema = line.split(":")
    key = key.strip()
    type_schema = type_schema.strip()

    if has_legacy_elements(type_schema):
        kwargs = extract_legacy_type_notation(type_schema)
    else:
        kwargs = extract_type_notation(type_schema)

    return {"key": key, **kwargs}


def extract_type_notation(type_schema: str):
    """Parse input and output notations from templates.

    notation schema: <type, rule=value, options=[option1, option2], default=value, ...>
    legacy schema: <type (rule|options|validation)> = default
    """
    kwargs = {}
    type_schema = re.match(r"<\s*(.*)\s*>", type_schema).group(1)
    # split on commas not inside quotes, brackets, or parentheses
    args = re.split(r',\s(?![^\[]*]|[^(]*\)|[^=\']*\'|[^="]*")', type_schema)

    kwargs["type"] = remove_outer_quotes(args.pop(0))

    if not args:
        return kwargs

    for arg in args:
        key, value = arg.split("=")[0], "=".join(arg.split("=")[1:])
        kwargs[key] = value

    return kwargs


def parse_custom_input_notation(line) -> dict:
    """Parse custom input and output notations from templates.

    In order to stay yaml compatible, a key should be present in the schema. The value may contain multiple placeholders.
    So the schema will exclude all but the first placeholder from forming a new line in final prompt format.
    """
    keys = re.findall(pattern=r"\{.+?\}", string=line)
    custom_template = ":".join(line.split(":")[1:])

    return {"type": "any", "custom_value_template": custom_template, "placeholder": keys}


def parse_key_value_notation(line: str) -> dict:
    """Parse input and output notations from templates.

    notation schema: key: {placeholder}
    Mainly used in input schema.
    """
    key, placeholder = line.split(":")
    key = key.strip()
    placeholder = re.findall(pattern=r"\{.+?\}", string=line)
    return {"key": key, "placeholder": placeholder, "type": "any"}


# === Legacy ===

def has_legacy_elements(type_schema: str) -> bool:
    if re.search(r"<.*=.*>", type_schema):
        return False
    return "> =" in type_schema or ">=" in type_schema
