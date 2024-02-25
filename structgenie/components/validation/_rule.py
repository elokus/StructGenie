"""Validation rules in template strings.

This module contains functions that can be used in template strings to validate
the output of a task.

Rules:
    - one_of: Check if the output is one of the possible values.
    - length: Check if the output has the correct length.
    - regex: Check if the output matches a regex pattern.
    - for each: Check if the output is one of the possible values for each item in a list.
    - if: Check if the output is one of the possible values if a condition is met.

"""
import re
from typing import Union

from structgenie.components.validation._varkey import get_key_from_config
from structgenie.utils.parsing.string import format_as_variable, is_none


def is_equal(value, rule):
    val_value = rule.split("=")[1].strip()
    if val_value.startswith("$"):
        return None
    elif val_value == value:
        return None
    return f"Output '{value}' is not equal to '{val_value}'."


def validate_rules(key: str, value: Union[str, list], val_config) -> Union[str, None]:
    key = get_key_from_config(key, val_config)
    rule = val_config[key].get("rule", None)
    options = val_config[key].get("options", None)
    if options:
        if val_config[key]["multiple_select"]:
            return one_or_more(value, parse_list(options))
        return one_of(value, parse_list(options))

    if rule:
        if rule.startswith("="):
            return is_equal(value, rule)
        elif rule.startswith("length"):
            return validate_length(value, rule)
        elif rule.startswith("one of"):
            possible_values = rule.split(":")[1].strip()
            return one_of(value, parse_list(possible_values))
        elif rule.startswith("one or more"):
            possible_values = rule.split(":")[1].strip()
            return one_or_more(value, parse_list(possible_values))
        elif rule.startswith("regex"):
            pattern = rule.split(":")[1].strip()
            return regex(value, pattern)
        elif rule.startswith("for each"):
            match = re.match(r"for each (.*) in (.*)", rule)
            iterator = match.group(1)
            possible_values = parse_list(match.group(2))
            iter_values = _find_iterator_values(key, iterator, val_config)
            is_iter_key = _is_iterator_key(key, iterator, val_config)
            return for_each(value, iter_values, is_iter_key, possible_values)
        elif rule.startswith("min=") or rule.startswith("max="):
            return min_max(value, rule)
        elif rule.startswith("if"):
            pass
        else:
            return None
    return None


def parse_list(value: Union[str, list]) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return parse_list(eval(value))
        except:
            return [v.strip() for v in value.split(",")]
    raise ValueError(f"Value '{value}' is not a list or a string.")


def one_of(output: str, possible_values: list[str]):
    if is_none(output) and (None in possible_values or "None" in possible_values):
        return None
    if output not in possible_values:
        return f"Output '{output}' is not one of the possible values: {possible_values}"
    return None


# TODO: add optional flag
def one_or_more(output: Union[str, list], possible_values: list[str]):

    if is_none(output) and (None in possible_values or "None" in possible_values):
        return None

    if isinstance(output, str):
        output = parse_list(output)

    if is_none(output):
        output = [None]

        # if None in possible_values:
        #     return None
        #return f"Output '{output}' is not one of the possible values: {possible_values}"
    if not all([o in possible_values for o in output]):
        return f"Output '{output}' does not contain one or more of possible values: {possible_values}"
    return None


def regex(output: str, pattern: str):
    if not re.match(pattern, output):
        return f"Output '{output}' does not match pattern: {pattern}"
    return None


def for_each(output: list, iterator_values: list[list], is_iter_key: bool, possible_values: list[str]):
    output = [] if is_none(output) else output
    if len(output) != len(possible_values):
        return f"Length of output '{output}' does not match length of possible values: {possible_values}"

    if is_iter_key:
        for i, iter_ in enumerate(possible_values):
            iter_ = format_as_variable(iter_)
            if not _iterator_in_output_keys(output, iter_, iterator_values):
                return f"Output '{output}' does not contain '{iter_}' for iterator '{iterator_values}'"

    if iterator_values:
        for i, iter_ in enumerate(possible_values):
            iter_ = format_as_variable(iter_)
            if not _iterator_in_output(output, iter_, iterator_values):
                return f"Output '{output}' does not contain '{iter_}' for iterator '{iterator_values}'"
    return None


def min_max(output: Union[str, int, float], rule: str):
    """Validate the length of the output."""
    if isinstance(output, str):
        try:
            output = float(output)
        except:
            output = int(output)

    min_ = re.search(r"min=(\d+)", rule).group(1)
    max_ = re.search(r"max=(\d+)", rule).group(1)
    if output < int(min_):
        return f"Output '{output}' is smaller than min: {min_}"
    if output > int(max_):
        return f"Output '{output}' is larger than max: {max_}"
    return None


def validate_length(output: Union[str, list], rule: str):
    """Validate the length of the output."""
    if isinstance(output, str):
        output = parse_list(output)
    length = rule.split("=")[1].strip()
    if len(output) != int(length):
        return f"Length of output '{output}' does not match length: {length}"
    return None


def _find_iterator_values(key: str, iterator: str, validation_config: dict):
    """find iterator '$...' variable in validation config and return the keys."""
    keys = []
    for val_key, value in validation_config.items():
        if val_key.startswith(f"{key}."):
            if value["rule"] and value["rule"] == f"={iterator}":
                keys.append(val_key.split(".")[1:])
    return keys


def _is_iterator_key(key: str, iterator: str, validation_config: dict):
    """find iterator '$...' variable in validation config and return the keys."""
    if f"{key}.{iterator}" in validation_config:
        return True
    return False


def _iterator_in_output(output: list[dict], iter_value, iterator_keys: list[list]):
    """Search for the current iter_value in the output_list."""
    for obj in output:
        if _iterator_in_object(obj, iter_value, iterator_keys):
            return True
    return False


def _iterator_in_output_keys(output: list, iter_value, iterator_keys: list[list]):
    """Search for the current iter_value in the output_list."""
    for obj in output:
        if iter_value in obj:
            return True
    return False


def _iterator_in_object(output: dict, iter_value, iterator_keys: list[list]):
    """Search for the current iter_value in the output_object."""
    for keys in iterator_keys:
        obj = output.copy()
        if len(keys) > 1:
            for key in keys:
                obj = obj[key]
        else:
            obj = obj[keys[0]]
        if obj != iter_value:
            return False

    return True
