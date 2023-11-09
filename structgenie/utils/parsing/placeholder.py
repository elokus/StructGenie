import re


def has_placeholder(text: str):
    """Check if text has placeholder."""
    return bool(re.search(r"{.*?}", text, re.DOTALL))


def replace_placeholder(template: str, set_tags: bool = False, with_end_tag: bool = False, **kwargs):
    for key, value in kwargs.items():
        if not value:
            value = ""
        elif set_tags:
            value = _parse_section_in_tags(value, key, with_end_tag=with_end_tag)
        template = template.replace(f"{{{key}}}", str(value))
    return template


def parse_section_placeholder(template, set_tags=True, with_end_tag: bool = False, **kwargs):
    return replace_placeholder(template, set_tags=set_tags, with_end_tag=with_end_tag, **kwargs)


def _parse_section_in_tags(content: str, tag: str, with_end_tag: bool = False):
    start_tag = f"# {tag.replace('_', ' ').capitalize()}"
    end_tag = f"# {tag.replace('_', ' ').capitalize()} end ==="
    if with_end_tag:
        section = f"{start_tag}\n\n{content}\n\n{end_tag}"
    else:
        section = f"{start_tag}\n\n{content}\n\n"
    return section


def replace_placeholder_in_dict(d: dict, **kwargs):
    for key, value in d.items():
        if isinstance(value, dict):
            d[key] = replace_placeholder_in_dict(value, **kwargs)
        elif isinstance(value, str):
            d[key] = replace_placeholder(value, **kwargs)
    return d
