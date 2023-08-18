import os

from structgenie.templates.functions import load_from_file


def template_mapping() -> dict:
    file_dir = os.path.join(os.path.dirname(__file__), "default_templates")
    files = os.listdir(file_dir)
    return {
        file.replace(".txt", ""): os.path.join(file_dir, file)
        for file in files
    }


DEFAULT_TEMPLATES = template_mapping()


def load_default_template(template_key: str) -> str:
    """Load default template from template_key."""
    if template_key in DEFAULT_TEMPLATES:
        return load_from_file(DEFAULT_TEMPLATES[template_key])
