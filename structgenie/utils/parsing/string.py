import re
from typing import Union, Any

import yaml


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def parse_yaml_string(s: str) -> Union[dict, yaml.YAMLError]:
    match = re.match(r"^.*```yaml(.*)```.*$", s, re.DOTALL)
    if match:
        s = match.group(1)
    result = yaml.safe_load(s)
    return _format_keys(result)


def parse_yaml_string_fix(s: str, output_keys: list[str] = None) -> Union[dict, yaml.YAMLError]:
    return _format_keys(parse_yaml_string(s), output_keys)


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
    string = yaml.dump(_d, sort_keys=sort_keys, Dumper=NoAliasDumper)
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


def parse_multi_line_string(s: str, key_pairs: list[tuple], keys: list) -> dict:
    """Parses a multi-line string with key pairs.

    Args:
        s (str): The string to parse.
        key_pairs (list[tuple]): A list of multi-line key and its next key.
    """

    def extract_multiline_text(text: str, key: str, next_key: str):
        if next_key:
            return re.search(f"\n{key}:(.*)\n{next_key}:", text, re.DOTALL).group(1).strip()
        return re.search(f"\n{key}:(.*)", text, re.DOTALL).group(1).strip()

    def remove_multiline_section(text: str, key: str, next_key: str):
        if next_key:
            return re.sub(fr"{key}:(.|\n)*{next_key}:", f"{next_key}:", text, re.DOTALL)
        return re.sub(fr"{key}:(.|\n)*", "", text, re.DOTALL)

    d = {}
    text = s
    keys_ = [key for key in keys]
    for key, next_key in key_pairs:
        key_ = format_as_key(key)
        next_key_ = format_as_key(next_key) if next_key else None
        d[key] = extract_multiline_text(s, key_, next_key_)
        text = remove_multiline_section(text, key_, next_key_)
        keys_.remove(key)

    if text.strip() and keys_:
        d.update(parse_yaml_string(text))
    return d
