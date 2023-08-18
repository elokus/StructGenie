import re
from typing import Union

from structgenie.base import BaseOutputModel, BaseOutputAttribute
from structgenie.input_output._template import _extract_from_groupdict
from structgenie.operator import get_loop_config


def validation_config_from_output_schema(output_schema: Union[dict, list]) -> dict:
    """return validation config from output schema"""

    def get_item_config(string: str):
        d = re.search(r"<(?P<type>[^\s]*)\s*(?P<rule>\(.*\))?\s*>\s*(?P<default>=.*?)?$", string).groupdict()
        return _extract_from_groupdict(d)

    for key, value in output_schema.items():
        pass

    return output_schema


def build_output_schema(output_model: BaseOutputModel, parent_key: str = None, replace_dict: dict = None,
                        inputs: dict = None):
    if inputs:
        replace_dict = _replace_dict_from_inputs(inputs, replace_dict)
        # print("Replace dict: ", replace_dict)

    if parent_key:
        # print("Init function", parent_key)
        attributes = output_model.get_nested_attr(parent_key, exclude_parent=True)
        output_type = output_model.get(parent_key).type
    else:
        attributes = output_model.attributes
        output_type = "dict"

    if output_type == "dict":
        output = {}
        for attr in attributes:
            key = _parse_key(attr.key, parent_key, replace_dict)
            if is_child_key(key):
                continue

            if is_loop(attr.rule):
                output[key] = build_output_from_loop(output_model, attr.key, replace_dict)

            elif attr.type == "dict" or attr.type == "list":
                # print(f"(dict) Parent key: {parent_key}, parsed_key: {key}"
                output[key] = build_output_schema(output_model, attr.key, replace_dict)
            else:
                output[key] = _output_item_value(attr, replace_dict)

    elif output_type == "list":
        output = []
        for attr in attributes:
            key = _parse_key(attr.key, parent_key, replace_dict)
            if is_child_key(key):
                continue
            if is_loop(attr.rule):
                output.append(build_output_from_loop(output_model, attr.key, replace_dict))
            # print(f"(list) Parent key: {parent_key}, parsed_key: {key}")
            elif attr.type == "dict":
                output.append({key: build_output_schema(output_model, attr.key, replace_dict)})
            elif attr.type == "list":
                output.append(build_output_schema(output_model, attr.key, replace_dict))
            else:
                output.append({key: _output_item_value(attr, replace_dict)})

    else:
        output = _output_item_value(output_model.get(parent_key), replace_dict)
    # print(f"Return for '{parent_key}': ", output)
    return output


def _replace_dict_from_inputs(inputs: dict, replace_dict: dict = None) -> dict:
    replace_dict = replace_dict or {}
    replace_dict.update({f"{{{k}}}": v for k, v in inputs.items()})
    return replace_dict


def _output_item_value(attr: BaseOutputAttribute, replace_dict: dict = None) -> str:
    if attr.rule and not attr.rule.startswith("for"):
        value = f"<{attr.type} ({attr.rule})>"
    else:
        value = f"<{attr.type}>"
    if attr.default:
        value = value + f"={attr.default}"
    if replace_dict:
        return replace_by_dict(value, replace_dict)
    return value


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
            string = string.replace(k, v)
    return string


def build_output_from_loop(output_model: BaseOutputModel, parent_key: str, replace_dict: dict = None):
    parent = output_model.get(parent_key)
    iter_key, iter_values = get_loop_config(parent.rule, **replace_dict)

    if parent.type == "list":
        output = []
        for x in iter_values:
            _replace_dict = replace_dict.copy()
            _replace_dict[iter_key] = x
            iter_output = build_output_schema(output_model, parent_key, replace_dict=_replace_dict)
            output.extend(iter_output)
        return output

    elif parent.type == "dict":
        output = {}
        for x in iter_values:
            _replace_dict = replace_dict.copy()
            _replace_dict[iter_key] = x
            output.update(build_output_schema(output_model, parent_key, replace_dict=_replace_dict))
        return output
    else:
        raise ValueError(f"Parent type '{parent.type}' not supported for loops")
