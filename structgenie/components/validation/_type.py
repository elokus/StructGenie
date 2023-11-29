import re
from typing import Union, Optional, List

from structgenie.components.validation._varkey import get_key_from_config
from structgenie.utils.parsing.string import is_none


def instance_type(type_):
    if re.match(r"(.*)\[(.*)\]", type_):
        if re.match(r"Union\[(.*)\]", type_):
            types = []
            for t in re.match(r"Union\[(.*)\]", type_).group(1).split(","):
                t_ = instance_type(t)
                if t_ and t_.strip() not in types:
                    types.append(t_.strip())
            if len(types) == 1:
                return types[0]
            return "Union[" + ", ".join(types) + "]"

        if re.match(r"Optional\[(.*)\]", type_):
            return "Optional[" + instance_type(re.match(r"Optional\[(.*)\]", type_).group(1)) + "]"

        if re.match(r"(.*)\[(.*)\]", type_).group(1) not in ["Union", "Optional"]:
            return re.match(r"(.*)\[(.*)\]", type_).group(1)
    return type_


def validate_type(key: str, value: str, val_config: dict) -> Union[str, None]:
    _key = get_key_from_config(key, val_config)
    type_ = val_config.get(_key).get("type", None)
    if is_none(value):
        return None
    if type_ == "any":
        return None
    try:
        if type_ and not isinstance(value, eval(instance_type(type_))):
            return f"Wrong type for '{key}': '{value}'. Expected {type_}, got {type(value)}"
    except:
        print(f"Isinstance failed for '{key}': '{value}'.Type: {type_}")
        raise ValueError(f"Wrong type for '{key}': '{value}'. on isinstance({instance_type(type_)})")
    return None

