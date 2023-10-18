from typing import Union

from structgenie.base import BaseExample


def type_schema_from_examples(examples: list[BaseExample], target: str = "output", **kwargs):
    """Create a type schema from a list of examples.

    Args:
        examples (list[BaseExample]): A list of examples.
        target (str, optional): The target type ["input", "output"]. Defaults to "output".
        kwargs: Additional keyword arguments to pass to the type schema.
            key: (str) The key to add to the type schema.
            value: (dict) {"rule":..., "default":...} to add to the type schema.
    """

    type_dict = type_dict_from_examples(examples, target=target)
    type_schema = {k: {"type": v} for k, v in type_dict.items()}
    if kwargs:
        for key, value in kwargs.items():
            type_schema[key].update(value)

    return type_schema


def type_dict_from_examples(examples: list[BaseExample], target: str = "output"):
    """Create a type schema from a list of examples.

    Args:
        examples (list[BaseExample]): A list of examples.
        target (str, optional): The target type ["input", "output"]. Defaults to "output".

    Returns:
        dict: A type schema.
    """
    type_mapping = _type_mapping_from_examples(examples, target)
    type_schema = {}
    for key, types in type_mapping.items():
        type_schema[key] = _type_from_mapping(types)
    return type_schema


def _type_mapping_from_examples(examples: list[BaseExample], target: str = "output"):
    """Create a dictionary of types from a list of examples.

    Args:
        examples (list[BaseExample]): A list of examples.
        target (str, optional): The target type. Defaults to "output".

    Returns:
        dict: A dictionary of types.
    """
    type_mapping = {}
    for example in examples:
        if target == "output":
            types = example.output_types
        elif target == "input":
            types = example.input_types
        else:
            raise ValueError(f"Target must be either 'input' or 'output'. Got {target}.")

        for key, type_ in types.items():
            if key not in type_mapping:
                type_mapping[key] = set()
            type_mapping[key].add(type_)

    return {key: list(value) for key, value in type_mapping.items()}


def _value_mapping_from_examples(examples: list[BaseExample], target: str = "output"):
    """Create a dictionary of types from a list of examples.

    Args:
        examples (list[BaseExample]): A list of examples.
        target (str, optional): The target type. Defaults to "output".

    Returns:
        dict: A dictionary of types.
    """
    type_mapping = {}
    for example in examples:
        if target == "output":
            types = example.output_types
        elif target == "input":
            types = example.input_types
        else:
            raise ValueError(f"Target must be either 'input' or 'output'. Got {target}.")

        for key, in types.items():
            if key not in type_mapping:
                type_mapping[key] = set()
            type_mapping[key].add(types[key])

    return {key: list(value) for key, value in type_mapping.items()}


def _type_from_mapping(types: list[Union[str, None]]):
    """Get the type from a type mapping.

    Args:
        types (dict): A type mapping.

    Returns:
        str: The formatted type in pydantic, typing syntax.
    """
    if len(types) == 1:
        return types[0]
    if None in types:
        types.remove(None)
        types.append("None")

    return f"Union[{', '.join(types)}]"
