"""Parse input and output notations from templates."""

import re


# === match multiline notation ===


def is_multiline_notation(text: str) -> bool:
    """Check if one line of input text is multiline notation.

    Multiline notation is defined as:
        'key':\n{placeholder}
    """
    return bool(re.match(r"(.*):\s?$", text))


def is_multiline_input(text: str):
    return bool(re.match(r"(.*):\s?\n\{.*}", text))


# === match text notation ===

def any_is_type_notation(text: str) -> bool:
    """Check if one line of input text is prompt syntax.

    type schema notation is defined as:
        'key': <type (rule)> = default
    """
    return any([is_type_notation(line) for line in text.splitlines()])


def any_is_input_notation(text: str) -> bool:
    """Check if one line of input text is input notation.

    Input schema notation is defined as:
        'key': /{placeholder}
        'key': {placeholder} {suffix}
        'key': {placeholder} = default
        'key': {placeholder} (rule) = default
    """
    return any([is_input_notation(line) for line in text.splitlines()])


# === match line notation === 

def is_type_notation(line: str) -> bool:
    return bool(re.match(r"(.*): <(.*)>", line))


def is_input_notation(line: str) -> bool:
    if is_type_notation(line):
        return False
    return is_key_value_notation(line) or is_custom_input_notation(line) or is_placeholder_only(line)


# === match input notation ===

def is_placeholder_only(line: str) -> bool:
    return bool(re.match(r"^\{.*}$", line.strip()))


def is_key_value_notation(line: str) -> bool:
    return bool(re.match(r"(.*): \{.*}", line))


def is_custom_input_notation(line: str) -> bool:
    if _is_not_key_value_notation(line):
        return True
    if _is_multi_placeholder(line):
        return True
    if _is_placeholder_with_suffix(line):
        return True
    if _is_placeholder_with_prefix(line):
        return True
    if _is_multiline_placeholder(line):
        return True
    return False


def _is_not_key_value_notation(line: str) -> bool:
    return bool(re.search(r"(?<!:\s)\{.*}", line))


def _is_placeholder_with_suffix(line: str) -> bool:
    return bool(re.search(r"\{.*}\s*\S+", line))


def _is_placeholder_with_prefix(line: str) -> bool:
    return bool(re.search(r"\S+\s*\{.*}", line))


def _is_multiline_placeholder(line: str) -> bool:
    return bool(re.search(r"\n\{.*}", line))


def _is_multi_placeholder(line: str) -> bool:
    return bool(len(re.findall(r"\{.*}", line)) > 1)
