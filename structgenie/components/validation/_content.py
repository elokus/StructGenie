from typing import Union

from structgenie.components.validation._varkey import get_key_from_config
from structgenie.utils.parsing.string import is_none


def validate_content(key: str, value: str, val_config: dict) -> Union[str, None]:
    """Check if content is not a placeholder '<str>'."""
    _key = get_key_from_config(key, val_config)
    type_ = val_config.get(_key).get("type", None)
    if is_none(value):
        return None
    if isinstance(value, list):
        failed = []
        for item in value:
            if isinstance(item, str) and (item.startswith(f"<str") or item.startswith(f"< str")):
                failed.append(item)
        if failed:
            return f"For '{key}'s list items placeholder were returned {failed}. Please generate a string for each item instead."
    if isinstance(value, str) and (value.startswith(f"<{type_}") or value.startswith(f"< {type_}")):
        return f"For '{key}' a placeholder was returned. Please generate a string for this key instead."
    return None
