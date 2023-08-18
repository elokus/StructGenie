from typing import Union


def validation_config_nested(key: str, val_config: dict) -> dict:
    return {k.replace(f"{key}.", ""): v for k, v in val_config.items() if k.startswith(f"{key}.")}


def required_keys(validation_config: dict):
    return [
        key for key in validation_config.keys()
        if
        not validation_config[key].get("type", "").startswith("Optional") and "." not in key and not key.startswith("$")
    ]


def validate_keys(d: dict, val_config: dict) -> Union[str, None]:
    missing_keys = [key for key in required_keys(val_config) if key not in d]
    for key in missing_keys:
        if key in val_config and val_config[key].get("default", None):
            missing_keys.remove(key)
    if missing_keys:
        return f"Keys {missing_keys} not in output"
    return None


def is_nested(key, val_config) -> bool:
    if validation_config_nested(key, val_config):
        return True
    return False
