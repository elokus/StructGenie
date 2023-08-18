import re
import inspect
from importlib import import_module

import typing

TYPE_DICT = {
    "string": "str",
    "integer": "int",
    "float": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
    "null": "None",
}

MAIN_TYPES = ["str", "int", "float", "bool", "list", "dict", "None"]


def parse_type_from_string(type_: str) -> str:
    if "List" in type_:
        type_ = type_.replace("List", "list")
    if "Dict" in type_:
        type_ = type_.replace("Dict", "dict")
    if "Any" in type_:
        type_ = type_.replace("Any", "any")

    if type_ in TYPE_DICT:
        return TYPE_DICT[type_]

    return type_.replace("'", "").replace('"', "")


def get_type_dict_from_object(obj: any, prefix: str = ""):
    type_dict = {}
    type_dict_ = _get_type_from_value(obj)
    for key, value in type_dict_.items():
        key_ = prefix + key
        if _is_dict_or_class(value):
            type_dict[key_] = "dict"
            type_dict.update(get_type_dict_from_object(value, prefix=key_ + "."))
        elif isinstance(value, list):
            if _is_list_of_dicts(value):
                type_dict[key_] = "list[dict]"
                type_dict.update(get_type_dict_from_object(value[0], prefix=key_ + "."))
            else:
                type_dict[key_] = "list"
        else:
            type_dict[key_] = value
    return type_dict


def _is_class(value: any) -> bool:
    return inspect.isclass(type(value)) and hasattr(type(value), "__annotations__")


def _is_dict_or_class(value: any) -> bool:
    return isinstance(value, dict) or _is_class(value)


def _is_list_of_dicts(value: list) -> bool:
    if len(value) > 0:
        return _is_dict_or_class(value[0])
    return False


def _get_type_from_value(value: any):
    if isinstance(value, dict):
        return {key: _get_type_from_value(value) for key, value in value.items()}
    if isinstance(value, list) and len(value) > 0:
        item_type = _get_type_from_value(value[0])
        if isinstance(item_type, dict):
            return [item_type]
        return "list[{}]".format(item_type)
    return parse_type(type(value))


def _parse_class(value: type):
    return _parse_annotations(value.__annotations__)


def parse_type(value: type):
    if inspect.isclass(value) and hasattr(value, "__annotations__"):
        return _parse_class(value)

    if isinstance(value, typing._GenericAlias):  # type: ignore
        return _parse_typing_type(value)

    if isinstance(value, type):
        return _parse_type(value)

    return parse_type(type(value))


def _parse_type(type_: type):
    match = re.match(r"<class '(.*)'>", str(type_)).group(1)
    if match in MAIN_TYPES:
        return match

    if match.startswith("typing."):
        return _parse_typing_type(match)


def _parse_typing_type(value: typing._GenericAlias):
    return str(value)


# def _import_object_from_type_string(string: str):
#     module_name, class_name = string.rsplit(".", 1)
#     module = import_module(module_name)
#     return getattr(module, class_name)


def _parse_annotations(annotations: dict):
    return {
        key: parse_type(value) for key, value in annotations.items()
    }
