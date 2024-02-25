from typing import Union

from structgenie.base import BaseIOModel, BaseIOLine
from structgenie.utils.operator import get_loop_config


def validation_config_from_output_schema(output_schema: Union[dict, list]) -> dict:
    """return validation config from output schema"""

    return output_schema


def build_output_schema(
        output_model: BaseIOModel, parent_key: str = None, replace_dict: dict = None, inputs: dict = None
) -> Union[dict, list, str]:
    if inputs:
        replace_dict = _replace_dict_from_inputs(inputs, replace_dict)
        # print("Replace dict: ", replace_dict)

    if parent_key:
        # print("Init function", parent_key)
        attributes = output_model.get_nested_attr(parent_key, exclude_parent=True)
        output_type = output_model.get(parent_key).safe_type
    else:
        attributes = output_model.lines
        output_type = "dict"

    if output_type == "dict":
        output = {}
        for attr in attributes:
            key = _parse_key(attr.key, parent_key, replace_dict)
            if is_child_key(key):
                continue

            if is_loop(attr.rule):
                output[key] = build_output_from_loop(output_model, attr.key, replace_dict)

            elif attr.type == "dict" or attr.type.startswith("dict"):
                # print(f"(dict) Parent key: {parent_key}, parsed_key: {key}"
                output[key] = build_output_schema(output_model, attr.key, replace_dict)
            elif attr.type == "list" or attr.type.startswith("list"):
                output[key] = build_output_schema(output_model, attr.key, replace_dict)
            else:
                output[key] = _output_item_value(attr, replace_dict)

    elif output_type == "list":
        output = []
        inner = {}
        if not attributes:
            if parent_key and (output_model.get(parent_key).rule or output_model.get(parent_key).options):
                return _output_item_value(output_model.get(parent_key), replace_dict)
            else:
                output.append("...")
        for attr in attributes:
            key = _parse_key(attr.key, parent_key, replace_dict)
            if is_child_key(key):
                continue
            if is_loop(attr.rule):
                output.append(build_output_from_loop(output_model, attr.key, replace_dict))
            # print(f"(list) Parent key: {parent_key}, parsed_key: {key}")
            elif attr.type == "dict":
                inner[key] = build_output_schema(output_model, attr.key, replace_dict)
            elif attr.type == "list":
                inner[key] = build_output_schema(output_model, attr.key, replace_dict)
            else:
                inner[key] = _output_item_value(attr, replace_dict)
        if inner:
            output.append(inner)

    else:
        output = _output_item_value(output_model.get(parent_key), replace_dict)

    if output == {} or output == []:
        output = _output_item_value(output_model.get(parent_key), replace_dict)
    # print(f"Return for '{parent_key}': ", output)
    return output


def _replace_dict_from_inputs(inputs: dict, replace_dict: dict = None) -> dict:
    replace_dict = replace_dict or {}
    replace_dict.update({f"{{{k}}}": v for k, v in inputs.items()})
    return replace_dict


def _output_item_value(attr: BaseIOLine, replace_dict: dict = None) -> str:
    string = f"<{attr.type}"
    if attr.options:
        if None in attr.options:
            attr.options.remove(None)
            attr.options.append("None")
        string += f", options=[{', '.join(attr.options)}]"
        if attr.multiple_select:
            string += ", multiple_select=True"

    if attr.rule and not attr.rule.startswith("for"):
        string += f", rule=({attr.rule})"
    string += ">"

    if attr.default:
        string += f"={attr.default}"
    if replace_dict:
        return replace_by_dict(string, replace_dict)
    return string


def _parse_key(key: str, parent_key: str = None, replace_dict: dict = None):
    if parent_key:
        key = key.replace(f"{parent_key}.", "")
    if replace_dict:
        key = replace_by_dict(key, replace_dict)
    return key


def is_child_key(key: str):
    return "." in key


def is_loop(rule: str | None):
    if not rule:
        return False
    return rule.strip().startswith("for")


def replace_by_dict(string: str, replace_dict: dict):
    for k, v in replace_dict.items():
        if k in string:
            string = string.replace(k, str(v))
    return string


def build_output_from_loop(output_model: BaseIOModel, parent_key: str, replace_dict: dict = None):
    parent = output_model.get(parent_key)
    replace_dict = replace_dict or {}
    iter_key, iter_values = get_loop_config(parent.rule, **replace_dict)

    if parent.type == "list" or parent.type.startswith("list"):
        output = []
        for x in iter_values:
            _replace_dict = replace_dict.copy()
            _replace_dict[iter_key] = x
            iter_output = build_output_schema(output_model, parent_key, replace_dict=_replace_dict)
            output.extend(iter_output)
        return output

    elif parent.type == "dict" or parent.type.startswith("dict"):
        output = {}
        for x in iter_values:
            _replace_dict = replace_dict.copy()
            _replace_dict[iter_key] = x
            output.update(build_output_schema(output_model, parent_key, replace_dict=_replace_dict))
        return output
    else:
        raise ValueError(f"Parent type '{parent.type}' not supported for loops")
