def get_key_from_config(key: str, config: dict) -> str:
    """return placeholder key if key = $placeholder and placeholder is in config.keys() else return key"""
    if not config.get(key, None) and any([k.startswith("$") for k in config.keys()]):
        if config.get(f"${key}", None):
            return f"${key}"
        return [k for k in config.keys() if k.startswith("$")][0]
    return key
