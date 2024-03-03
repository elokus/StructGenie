import re
from typing import Union, Optional, List

from structgenie.components.validation._varkey import get_key_from_config
from structgenie.utils.parsing.string import is_none


def instance_type(type_):
    """Converts a string type to an instance type.

    Removes nested generic types and replaces them with the correct type to run with isinstance(x, eval(type_str)).

    Args:
        type_ (str): A string representing a type.
    Returns:
        str: A string representing the instance type.
    """

    def parse_union(string: str):
        types = []
        for t in re.match(r"Union\[(.*)\]", string).group(1).split(","):
            if t.endswith(']'):
                t = t[:-1]
            t_ = instance_type(t)
            if t_ and t_.strip() not in types:
                types.append(t_.strip())
        if len(types) == 1:
            return types[0]
        types = [instance_type(t) for t in types if t]
        return "Union[" + ", ".join(types) + "]"

    def parse_optional(string: str):
        t = re.match(r"Optional\[(.*)\]", string).group(1)
        return "Optional[" + instance_type(t) + "]"

    def parse_generic(string: str):
        t = re.match(r"(.*)\[(.*)\]", string).group(1)
        if "[" in t:
            return t.split("[")[0]
        return t

    if "[" in type_ and not "]" in type_:
        return type_.split("[")[0]

    if re.match(r"(.*)\[(.*)\]", type_):
        if re.match(r"Union\[(.*)\]", type_):
            return parse_union(type_)

        if re.match(r"Optional\[(.*)\]", type_):
            return parse_optional(type_)

        return parse_generic(type_)

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
        if instance_type(type_) == "datetime.datetime":
            return verify_date(key, value)
        print(f"Isinstance failed for '{key}': '{value}'.Type: {type_}")
        raise ValueError(f"Wrong type for '{key}': '{value}'. on isinstance({instance_type(type_)})")
    return None


def verify_date(key, value):
    from datetime import datetime

    if isinstance(value, datetime):
        return None

    for format in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"]:
        try:
            date = datetime.strptime(value, format)
            return None
        except:
            pass

    return f"Wrong date format for '{key}': '{value}'. Expected %Y-%m-%d, got {value}, type: {type(value)}"



if __name__ == "__main__":
    str_types = [
        "list[Optional[str, None]]",
        "list[Union[str, None]]",
        "list[str]",
        "Optional[str]",
        "Union[str, None]",
        "Optional[Union[str, None]]",
        "Union[Optional[str, None]]",
        "Optional[List[str]]",
        "Union[List[str], None]",
        ]

    for str_type in str_types:

        print(instance_type(str_type)) # list[Union[str, None]]


    dates = ['2022-10-10', '2022-10-12 12:00:00', '2022-10-12 12:00:00.000000']

    for date in dates:
        print(verify_date("date", date))