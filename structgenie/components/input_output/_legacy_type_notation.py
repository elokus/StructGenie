import re

from structgenie.utils.parsing.string import remove_outer_quotes


def extract_legacy_type_notation(type_schema: str):
    d = re.search(r"<(?P<type>[^\s]*)\s*(?P<rule>\(.*\))?\s*>\s*(?P<default>=.*?)?$", type_schema).groupdict()
    return extract_type_notation(d)


def extract_type_schema_from_text(text: str):
    output_dict = {}
    for line in text.splitlines():
        d = re.search(r"(?P<key>.*)\s*:\s*<(?P<type>[^\s]*)\s*(?P<rule>\(.*\))?\s*>\s*(?P<default>=.*?)?$",
                      line).groupdict()
        output_dict[d["key"]] = extract_type_notation(d)
    return output_dict


def extract_type_notation(d: dict):
    line_dict = {"type": d["type"], "rule": None, "default": None}

    if d["rule"]:
        line_dict["rule"] = re.match(r"\((.*)\)", d["rule"]).group(1)

    if d["default"]:
        default = re.match(r"=\s*(.*)$", d["default"]).group(1).strip()
        if default.startswith("{") and default.endswith("}"):
            default = eval(default)
        elif default.startswith("[") and default.endswith("]"):
            default = eval(default)
        line_dict["default"] = remove_outer_quotes(default)
    return line_dict
