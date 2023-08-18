"""Load system instruction from template"""
from structgenie.parser.inputs import load_placeholder_if_exist
from structgenie.templates import functions


def load_and_call_system_function(system_instruction: str, inputs: dict = None, **kwargs):
    """Load system instruction from string.

    Example input:
        system_instruction = "load_from_file: path/to/file, encoding='utf-8'"
    """
    function_name, args, kwargs = parse_system_instruction(system_instruction, inputs, **kwargs)
    return _load_and_call_function(function_name, args, kwargs)


def parse_system_instruction(system_instruction: str, inputs: dict, **kwargs):
    """Parse system instruction into function name and arguments.

    Example input:
        system_instruction = "load_from_file: path/to/file, encoding='utf-8'"
    """
    function_name, arguments = system_instruction.split(":")
    args, kwargs = _parse_arguments(arguments, inputs, **kwargs)
    return function_name, args, kwargs


def _parse_arguments(arguments: str, inputs: dict, **kwargs):
    args = []
    kwargs_ = {}
    for argument in arguments.split(","):
        if "=" in argument:
            key, value = argument.split("=")
            kwargs_[key.strip()] = load_placeholder_if_exist(value.strip(), inputs, **kwargs)
        else:
            args.append(load_placeholder_if_exist(argument.strip(), inputs, **kwargs))
    return args, kwargs_


def _load_and_call_function(function_name: str, args: list[str], kwargs: dict[str, str] = None):
    """Load function from function name and arguments."""
    function = getattr(functions, function_name)
    return function(*args, **kwargs)
