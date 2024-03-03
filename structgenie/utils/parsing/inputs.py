import re
from typing import Union

from structgenie.pydantic_v1 import BaseModel

from structgenie.utils.parsing.placeholder import has_placeholder
from structgenie.utils.parsing.string import dump_to_yaml_string


# === Format inputs ===

def format_inputs(placeholder_mapping: dict):
    """Format to input schema or dump to yaml."""
    formatted_inputs = {}

    for placeholder, value in placeholder_mapping.items():
        key = re.match(r"{(.*)}", placeholder).group(1)

        formatted_inputs[key] = value_to_string(value)

    return formatted_inputs


# def format_inputs(placeholder_mapping: dict, input_schema: str):
#     """Format to input schema or dump to yaml."""
#     input_schema_placeholder = re.findall(r"{.*?}", input_schema, re.DOTALL)
#     formatted_inputs = {}
#     for placeholder, value in placeholder_mapping.items():
#         key = re.match(r"{(.*)}", placeholder).group(1)
#
#         if isinstance(value, BaseModel):
#             value = value.dict()
#
#         if isinstance(value, str):
#             formatted_inputs[key] = value
#             continue
#
#         elif isinstance(value, dict) or isinstance(value, list):
#             if value in input_schema_placeholder:
#                 formatted_inputs[key] = _format_input_schema_inputs(input_schema, placeholder, value)
#             else:
#                 formatted_inputs[key] = dump_to_yaml_string(value)
#
#         else:
#             try:
#                 formatted_inputs[key] = str(value)
#             except Exception as e:
#                 raise ValueError(f"Value of placeholder {key}: {value} cannot be converted to string. "
#                                  f"Unknown type: {type(value)}. Exception: {e}")
#
#     return formatted_inputs

# ToDo: remove
def dump_to_input_schema(input_schema, placeholder_mapping: dict):
    import re
    input_dict = {}
    for line in input_schema.split("\n"):
        key, value = line.split(":")
        key = key.strip()
        value = value.strip()
        if value in placeholder_mapping:
            value = placeholder_mapping[value]
        else:
            placeholders = re.findall(r"{.*?}", line, re.DOTALL)
            for placeholder in placeholders:
                if placeholder in placeholder_mapping:
                    value = value.replace(placeholder, value_to_string(placeholder_mapping[placeholder]))
        input_dict[key] = value
    return dump_to_yaml_string(input_dict)


def value_to_string(value):
    if isinstance(value, BaseModel):
        value = value.dict()

    if isinstance(value, str):
        return value

    elif isinstance(value, dict) or isinstance(value, list):
        return dump_to_yaml_string(value)

    else:
        try:
            return str(value)
        except Exception as e:
            raise ValueError(f"Value of placeholder {value} cannot be converted to string. "
                             f"Unknown type: {type(value)}. Exception: {e}")


# === Load inputs by placeholders ===


def prepare_inputs_placeholders(prompt: str, inputs: dict, **kwargs) -> tuple[str, dict]:
    """Load inputs by placeholders and execute system instructions if present"""
    prompt = load_system_placeholders(prompt, inputs, **kwargs)
    return _prepare_placeholders(prompt, inputs, **kwargs)


def load_placeholder_inputs(placeholder: str, inputs: dict, **kwargs):
    """Load placeholder from input schema."""
    key = re.match(r"{(.*)}", placeholder).group(1)
    return _pass_placeholder_key(key, inputs, **kwargs)


def load_placeholder_if_exist(placeholder: str, inputs: dict, **kwargs):
    """Load placeholder from input schema if it exists."""
    if has_placeholder(placeholder):
        return load_placeholder_inputs(placeholder, inputs, **kwargs)
    else:
        return placeholder


# === System placeholders ===

def load_system_placeholders(prompt: str, inputs: dict, **kwargs):
    match = re.findall(r"(\{\{!system.*?}})", prompt, re.DOTALL)

    if match:
        for system_placeholder in match:
            prompt = prompt.replace(
                system_placeholder,
                load_system_placeholder(system_placeholder, inputs, **kwargs)
            )
    return prompt


def load_system_placeholder(system_placeholder: str, inputs: dict, **kwargs):
    """Load system placeholder."""
    from structgenie.utils.templates.load_functions import load_and_call_system_function
    system_instruction = re.match(r"{{!system:(.*)}}", system_placeholder).group(1)
    return load_and_call_system_function(system_instruction, inputs, **kwargs)


# === Private functions ===


def _format_input_schema_inputs(input_schema: str, placeholder: str, value: Union[dict, list]):
    """Format input schema inputs."""
    # find line with placeholder
    for line in input_schema.splitlines():
        if placeholder in line:
            break

        if re.match(r"(.*?): ({.*?})", line):
            prefix = re.match(r"(.*?): ({.*?})", line).group(1)
            indent = (len(prefix) - len(prefix.lstrip())) / 2
            return "\n" + dump_to_yaml_string(value, indent=indent + 1)
        if re.match(fr"\s*- {re.escape(placeholder)}", line):
            indent = (len(line) - len(line.lstrip())) / 2
            return "\n" + dump_to_yaml_string(value, indent=indent)
        if re.match(re.escape(placeholder), line):
            return dump_to_yaml_string(value)
    return value


def _prepare_placeholders(prompt: str, inputs: dict, **kwargs) -> tuple:
    if "<%last_output%>" in prompt:
        prompt_ = prompt.split("<%last_output%>")[0]
    else:
        prompt_ = prompt
    match = re.findall(r"{.*?}", prompt_, re.DOTALL)
    placeholder_inputs = {}
    if match:
        for placeholder in match:
            placeholder_inputs[placeholder] = load_placeholder_inputs(placeholder, inputs, **kwargs)
    return prompt, placeholder_inputs


def _pass_placeholder_key(key: str, inputs: Union[dict, str], **kwargs):
    """Pass values from inputs and kwargs to placeholder."""
    if not inputs and not kwargs:
        raise ValueError(f"No inputs or kwargs passed to placeholder for loading {{key}}")

    if key == "inputs":
        return inputs

    if key == "input":
        # when inputs is a single argument
        if isinstance(inputs, str):
            return inputs
        # when multiple inputs are passed
        if isinstance(inputs, dict):
            if "input" in inputs:
                return inputs["input"]
            elif "input" in kwargs:
                return kwargs["input"]
            else:
                # when no "input" key is found in inputs or kwargs pass all inputs
                return inputs

    # load value placeholder is a dictionary
    match_dict = re.match(r"(.*)\[['\"](.*)['\"]]", key)
    if match_dict:
        if match_dict.group(1) == "inputs":
            return inputs[match_dict.group(2)]
        elif kwargs and match_dict.group(1) in kwargs:
            return kwargs[match_dict.group(1)][match_dict.group(2)]
        else:
            if match_dict.group(1) in inputs:
                return inputs[match_dict.group(1)][match_dict.group(2)]
    # load value placeholder is not a dictionary
    else:
        if key in inputs:
            return inputs[key]
        elif kwargs and key in kwargs:
            return kwargs[key]

    raise ValueError(f"Placeholder {key} not found in inputs or kwargs")


def replace_placeholder_from_inputs_and_kwargs(string: str, inputs: dict, **kwargs):
    """Replace placeholder with value."""
    placeholders = re.findall(r"{.*?}", string, re.DOTALL)
    for placeholder in placeholders:
        value = load_placeholder_inputs(placeholder, inputs, **kwargs)
        string = string.replace(placeholder, str(value))
    return string
