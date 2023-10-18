from structgenie.utils.parsing import replace_placeholder

SECTION_TAGS = {
    "SEPERATOR_STYLE": ['=== {section} ===', '=== {section} end ==='],
    "HTML_STYLE": ['<section {section}>', '</section {section}>'],
    "GUIDANCE_STYLE": ['{{#{section}~}}', '{{~/{section}}}'],
    "MARKDOWN_STYLE": ['# {section}', '# ---'],
}
SECTION_ALIASES = {
    "instruction": ["instructions", "instruction"],
    "examples": ["examples", "example"],
    "output_schema": ["response schema", "response model", "output model", "output schema", "output", "response"],
    "input_schema": ["input schema", "input model", "input"],
    "system_config": ["system configuration", "system config", "config"]
}


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
