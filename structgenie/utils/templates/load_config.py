from structgenie.utils.parsing import remove_quotes


def load_system_config(system_config: str) -> dict:
    """Load system config from string."""
    configs = {
        "partial_variables": {},
        "engine": {},
        "model": {},
        "prompt": {},
    }
    if not system_config:
        return configs

    for line in system_config.splitlines():
        line = line.strip()
        if line.startswith("$"):
            key, value = parse_partial_variables(line)
            configs["partial_variables"][key] = value
        elif line.startswith("!engine"):
            configs["engine"] = parse_kwargs(line)
        elif line.startswith("!model"):
            configs["model"] = parse_kwargs(line)
        elif line.startswith("!prompt"):
            configs["prompt"] = parse_kwargs(line)

    return configs


def parse_partial_variables(line):
    """Split partial variables from line and parse value by type."""
    key, value = line.split("=")
    type_ = "str"
    if ":" in key:
        key, type_ = key.split(":")
    if type_ == "list":
        value = [remove_quotes(value.strip()) for value in value.split(",")]
    elif type_ == "dict":
        value = {remove_quotes(k.strip()): remove_quotes(v.strip())
                 for k, v in [value.split(":") for value in value.split(",")]}
    return key.strip(), value.strip()


def parse_kwargs(line):
    """Split kwargs from line.

    Example input:
        line = "!engine: model_name = 'gpt2', model_size = 'small'"

    """
    configs = {}
    settings = line.split(":")[1]
    for setting in settings.split(","):
        key, value = setting.split("=")
        key = remove_quotes(key.strip())
        value = remove_quotes(value.strip())
        configs[key] = value
    return configs


def parse_model_kwargs(configs, line):
    pass


def parse_prompt_kwargs(configs, line):
    pass
