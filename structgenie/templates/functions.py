from structgenie.parser import dump_to_yaml_string


def load_from_file(path: str, encoding: str = "utf-8") -> str:
    """Load file from path."""
    with open(path, "r", encoding=encoding) as f:
        return f.read()


def parse_as_yaml(inputs: dict) -> dict:
    """Parse inputs as yaml."""
    return dump_to_yaml_string(inputs)
