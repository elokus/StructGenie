import yaml
from yaml.scanner import ScannerError

from typing import Union, Any


def parse_yaml_string(s: str) -> Union[dict, yaml.YAMLError]:
    result = _parse_yaml_string(s)
    if isinstance(result, yaml.YAMLError) or isinstance(result, ScannerError):
        return result

    return _format_keys(result)


def _parse_yaml_string(s: str):
    try:
        return yaml.safe_load(s)
    except yaml.YAMLError as exc:
        return exc


def parse_yaml_string_fix(s: str, output_keys: list[str] = None) -> Union[dict, yaml.YAMLError]:
    return _format_keys(_parse_yaml_string(s), output_keys)


def _format_keys(d: Any, as_lower_case: bool = True) -> Any:
    if isinstance(d, dict):
        if as_lower_case:
            d = {k.replace(" ", "_").lower(): v for k, v in d.items()}
        else:
            d = {k.replace("_", " ").capitalize(): v for k, v in d.items()}
        for key, value in d.items():
            d[key] = _format_keys(value)
    elif isinstance(d, list):
        for i, item in enumerate(d):
            d[i] = _format_keys(item)
    return d


def dump_to_yaml_string(d: Union[dict, list], indent=0, sort_keys=False) -> str:
    if isinstance(d, dict):
        _d = _format_keys(d, as_lower_case=False)
    else:
        _d = d
    string = yaml.dump(_d, sort_keys=sort_keys)
    if indent > 0:
        string = "\n".join("  " * indent + line for line in string.splitlines())
    return string


def remove_quotes(s: str) -> str:
    return s.replace('"', "").replace("'", "")


def remove_outer_quotes(s: str) -> str:
    try:
        s = s.strip()
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        if s.startswith("'") and s.endswith("'"):
            return s[1:-1]
        return s
    except:
        return s


def format_as_variable(key: str) -> str:
    return key.replace(" ", "_").lower()


def format_as_key(key: str) -> str:
    return key.replace("_", " ").capitalize()


def is_none(s: Union[str, list, dict]) -> bool:
    if not s:
        return True
    if isinstance(s, str) and s in ["none", "None", "NONE"]:
        return True
    if isinstance(s, list) and all([is_none(item) for item in s]):
        return True
    return False
