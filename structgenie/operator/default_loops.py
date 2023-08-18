from structgenie.errors import TemplateError
from structgenie.base import BaseOutputModel
from structgenie.parser.string import format_as_variable


def parse_default_in_loop(output: dict, output_model: BaseOutputModel, key: str, **kwargs):
    """Parse default values in loop objects"""

    if not has_defaults(output_model.get_nested_dict(key, full_key=False)):
        return output

    iterator, iter_values = get_loop_config(output_model.get(key).rule, **kwargs)

    if key == iterator:
        return _set_default_to_items(output, output_model, iter_values, key)

    if output_model.get(key).type == "dict":
        val_dict = output_model.get_nested_dict(key, full_key=False)
        if iterator not in val_dict:
            raise TemplateError(
                f"Invalid output schema for {iterator} loop in dict. {iterator} must be set as a key in {key} dict.")
        output[key] = _set_default_to_dict_loop(output.get(key, {}), output_model, iterator, iter_values, key)

    elif output_model.get(key).type == "list":
        output[key] = _set_default_to_list_loop(output.get(key, []), output_model, iterator, iter_values, key)

    return output


def has_defaults(val_dict: dict, key: str = None) -> bool:
    if key is None:
        return any([has_defaults(val_dict, key) for key in val_dict.keys()])
    return val_dict.get(key, {}).get("default") is not None


def has_loop(output_model: BaseOutputModel, key: str) -> bool:
    return output_model.get(key).rule is not None and output_model.get(key).rule.startswith("for")


def get_loop_config(rule: str, **kwargs) -> tuple[str, list]:
    """Get iterator and iterator values from rule"""
    import re
    for key, val in kwargs.items():
        if key.startswith("{") and key.endswith("}"):
            key = key[1:-1]
        rule = rule.replace(f"{{{key}}}", str(val))

    d = re.match(r".*(?P<iterator>\$[a-zA-Z0-9_]+)\sin\s(?P<iter_values>.*)$", rule).groupdict()

    return d["iterator"], eval(d["iter_values"])


def _set_default_to_items(output: dict, output_model, iter_values: list, key):
    """Set default values to items in loop where key is iterator.

    Example:
        >> template = '$task: <str (for each $task in ["collect", "analyze", "evaluate")> = "Task Name"'
        >> output = {"collect": "Collection Task", "analyze": "Analysis Task"}
        ...
        >> output = _set_default_to_items(output, template, ["collect", "analyze", "evaluate"], "$task")
        >> print(output)
        {"collect": "Collection Task", "analyze": "Analysis Task", "evaluate": "Task Name"}

    """
    for val in iter_values:
        val = format_as_variable(val)
        if output.get(val) is None:
            output[val] = output_model.get_default(key)
    return output


def _set_default_to_dict(output: dict, output_model: BaseOutputModel, parent_key: str, **kwargs):
    """Set default values to dict items in loop

    Loops through iter_values and creates key, value pairs in output dict where key is derived from iterator

    Args:
        output: dict to add default values to
        output_model: BaseOutputModel object
        parent_key: parent key in output_model to get nested values from
        kwargs: placeholder, value pairs to replace in default and keys

    """

    def replace_placeholder_in_default(value: dict, **kwargs):
        """Replace placeholder in default value"""
        if not kwargs:
            return value
        if value.get("default") is None:
            return value
        value["default"] = replace_placeholder(value["default"], **kwargs)
        return value

    def replace_placeholder(value: str, **kwargs):
        """Replace placeholder in key"""
        if not kwargs:
            return value
        for key, val in kwargs.items():
            value = value.replace(key, val)
        return value

    val_dict = output_model.get_nested_dict(parent_key, full_key=False)
    _val_dict = {replace_placeholder(format_as_variable(key), **kwargs): replace_placeholder_in_default(value, **kwargs)
                 for key, value in
                 val_dict.items()}

    for key, value in _val_dict.items():
        if value.get("default") is not None:
            if output.get(key) is None:
                output[key] = value["default"]
    return output


def _set_default_to_dict_loop(output: dict, output_model: BaseOutputModel, iterator: str, iter_values: list,
                              parent_key: str):
    """Set default values to dict items in loop

    Loops through iter_values and creates key, value pairs in output dict where key is derived from iterator
    """

    # loop through iter_values in replace iterator placeholder in keys in values to output
    for x in iter_values:
        x = format_as_variable(x)
        next_parent_key = f"{parent_key}.{iterator}"
        if output_model.get_default(next_parent_key) is not None:
            if output.get(x) is None:
                output[x] = output_model.get_default(next_parent_key)
        else:
            output[x] = _set_default_to_key(output.get(x, {}), output_model, iterator, iter_values, next_parent_key, x)

    return output


def _set_default_to_list_loop(output: list, output_model: BaseOutputModel, iterator: str, iter_values: list,
                              parent_key: str):
    """Set default values to list[dict] items  in loop

    Loops through iter_values and creates key, value pairs in output dict where key is derived from iterator
    """
    val_dict = output_model.get_nested_dict(parent_key, full_key=False)

    val_key = None
    if len(val_dict) > 1:
        for key, value in val_dict.items():
            if output_model.get_default(f"{parent_key}.{key}") == iterator:
                val_key = key
                break

    if val_key is None:
        return output

    output_list = []

    for x in iter_values:
        # find item by val_key
        item = [item for item in output if item.get(val_key) == x]
        if len(item) == 0:
            item = {}
        else:
            item = item[0]

        output_list.append(_set_default_to_dict(item, output_model, parent_key, **{iterator: x}))
    return output_list


def _set_default_to_key(output: dict, output_model: BaseOutputModel, iterator: str, iter_values: list, parent_key: str,
                        item_key: str):
    if output_model.get(parent_key).type == "dict":
        return _set_default_to_dict(output, output_model, parent_key, **{iterator: item_key})
    elif output_model.get(parent_key).type == "list":
        return _set_default_to_list_loop(output, output_model, iterator, iter_values, parent_key)

    default = output_model.get(parent_key).default
    if default:
        return default if default != iterator else item_key
    return None
