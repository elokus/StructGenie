from structgenie.parser import replace_placeholder
from structgenie.styles.tags import SECTION_TAGS, SECTION_ALIASES


def tag_in_string(tag: str, string: str) -> bool:
    """Check if tag is in string."""
    return tag in string


def section_in_string(string: str, section: str, include_aliases: bool = True) -> bool:
    """Check if section is in any of the possible tag styles in the string."""
    if include_aliases:
        section_keys = SECTION_ALIASES[section]
    else:
        section_keys = [section]

    possible_tags = [replace_placeholder(tag, section=key) for key in section_keys for tag in SECTION_TAGS]

    return any([tag_in_string(tag, string) for tag in possible_tags])
