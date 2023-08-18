import re

from structgenie.parser import remove_quotes
from structgenie.parser.string import remove_outer_quotes


def is_template_syntax(text: str) -> bool:
    """Check if one line of input text is template syntax.

    Template syntax is defined as:
        < 'key': type (rule) >
    """

    pattern = r"<\s*'(.*)':\s*(.*)\s*>"
    for line in text.splitlines():
        if re.match(pattern, line):
            return True

    return False


def is_prompt_syntax(text: str) -> bool:
    """Check if one line of input text is prompt syntax.

    Prompt syntax is defined as:
        'key': <type (rule)>
    """

    pattern = r"(.*): <(.*)>"
    for line in text.splitlines():
        if re.match(pattern, line):
            return True

    return False


def output_dict_from_template(text: str):
    output_dict = {}
    for line in text.splitlines():
        d = re.search(r"<\s*'(?P<key>.*)': (?P<type>[^\s]*)\s*(?P<rule>\(.*\))?\s*>\s*(?P<default>\s*=.*?)?$",
                      line).groupdict()
        output_dict[d["key"]] = _extract_from_groupdict(d)
        #
        # output_dict[d["key"]] = {"type": d["type"], "rule": None, "default": None}
        #
        # if d["rule"]:
        #     output_dict[d["key"]]["rule"] = re.match(r"\((.*)\)", d["rule"]).group(1)
        #
        # if d["default"]:
        #     default = re.match(r"=\s*[\"']?(.*)[\"']?", d["default"]).group(1).strip()
        #     if default.startswith("{") and default.endswith("}"):
        #         default = eval(default)
        #     elif default.startswith("[") and default.endswith("]"):
        #         default = eval(default)
        #     output_dict[d["key"]]["default"] = default

    return output_dict


def output_dict_from_prompt(text: str):
    output_dict = {}
    for line in text.splitlines():
        d = re.search(r"(?P<key>.*)\s*:\s*<(?P<type>[^\s]*)\s*(?P<rule>\(.*\))?\s*>\s*(?P<default>=.*?)?$",
                      line).groupdict()
        output_dict[d["key"]] = _extract_from_groupdict(d)
    return output_dict


def _extract_from_groupdict(d: dict):
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
