import re
from typing import Optional, Union

from structgenie.utils.templates.section_tags import SECTION_TAGS, SECTION_ALIASES

EXTRA_PATTERN = {
    "instruction": "^(?:\n)?(\w.*?)(?=\n\n|{next_start_prefix}|Begin!)",
    "input_schema": r"(?<=Begin!\n)(.*?)(?=---|$)",
    "output_schema": r"(?<=---\n)([^\n]*: <.*>(\s*=.*)?|<.*>(\s*=.*)?)+$"
}


def _detect_style(template: str, section_tags: dict = None) -> Optional[str]:
    """Detect which style has been used in the template."""
    if not section_tags:
        section_tags = SECTION_TAGS
    for style, (start_tag, end_tag) in section_tags.items():
        # Check if any section's start tag is present in the template
        for section in ["Instruction", "Examples", "Response schema", "Input schema"]:
            if start_tag.replace("{section}", section) in template:
                return style
    return _detect_style("# Instruction\n" + template)


def extract_sections(template: str) -> Optional[dict[str, str]]:
    """Extract sections from the template."""
    style = _detect_style(template)
    if style:
        return extract_sections_with_aliases(template, style)


def extract_section(template: str, section: str) -> Optional[str]:
    """Extract section from the template."""
    style = _detect_style(template)
    if style:
        return extract_sections_with_aliases(template, style, section)
    return None


def extract_sections_with_aliases(template: str, style: str, section: str = None) -> Union[dict[str, str], str]:
    """Extract sections from the template based on the provided style, considering aliases, using start tag prefixes."""
    extracted_sections = {}
    if section:
        section_aliases = {section: SECTION_ALIASES[section]}
    else:
        section_aliases = SECTION_ALIASES

    start_tag, end_tag = SECTION_TAGS[style]
    next_start_prefix = start_tag.split("{section}")[0]

    for section_key, aliases in section_aliases.items():
        # Add capitalized versions of each alias
        all_possible_names = aliases + [alias.capitalize() for alias in aliases] + [section_key]

        for possible_name in all_possible_names:

            # Create the start and end patterns based on the section_key alias or name using replace()
            start_pattern = start_tag.replace("{section}", possible_name)
            end_pattern = end_tag.replace("{section}", possible_name)

            # Extract the content between the start and end tags
            if end_pattern in template:  # Check if explicit end tag is used
                match = re.search(f"{re.escape(start_pattern)}(.*?){re.escape(end_pattern)}", template, re.DOTALL)
                if match:
                    extracted_sections[section_key] = match.group(1).strip()
                    break
            else:  # If no explicit end tag, extract till the next start tag prefix or end of string
                match = re.search(f"{re.escape(start_pattern)}(.*?){re.escape(next_start_prefix)}", template,
                                  re.DOTALL)
                if match:
                    extracted_sections[section_key] = match.group(1).strip()
                    break
                else:
                    # If no other start pattern is found, extract till the end
                    match = re.search(f"{re.escape(start_pattern)}(.*)", template, re.DOTALL)
                    if match:
                        extracted_sections[section_key] = match.group(1).strip()
                        break

        # If no section for instruction and input was found, try to extract the section from extra pattern
        if section_key not in extracted_sections and section_key in EXTRA_PATTERN:
            pattern = EXTRA_PATTERN[section_key].replace("{next_start_prefix}", re.escape(next_start_prefix))
            match = re.search(pattern, template, re.DOTALL)
            if match:
                extracted_sections[section_key] = match.group(1).strip()

    if "\n---\n" in extracted_sections["input_schema"]:
        extracted_sections["input_schema"] = extracted_sections["input_schema"].split("\n---\n")[0].strip()

    if section:
        return extracted_sections[section]

    return extracted_sections
