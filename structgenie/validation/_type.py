from typing import Union
import re

from structgenie.parser.string import is_none
from structgenie.validation._varkey import get_key_from_config


def instance_type(type_):
    if re.match(r"(.*)\[(.*)\]", type_):
        if re.match(r"(.*)\[(.*)\]", type_).group(1) not in ["Union", "Optional"]:
            return re.match(r"(.*)\[(.*)\]", type_).group(1)
    return type_


def validate_type(key: str, value: str, val_config: dict) -> Union[str, None]:
    _key = get_key_from_config(key, val_config)
    type_ = val_config.get(_key).get("type", None)
    if is_none(value):
        return None
    if type_ and not isinstance(value, eval(instance_type(type_))):
        return f"Wrong type for '{key}': '{value}'. Expected {type_}, got {type(value)}"
    return None
