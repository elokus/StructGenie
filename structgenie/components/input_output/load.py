from typing import Union

from structgenie.components.examples import ExampleSelector
from structgenie.components.input_output import OutputModel, InputModel


def init_output_model(
        output_model: Union[OutputModel, InputModel, dict, str] = None,
        examples: ExampleSelector = None,
        partial_output_model: dict[str, Union[OutputModel, dict, str]] = None,
        **kwargs
) -> Union[OutputModel, InputModel]:
    """Initialize output model from output_model or examples.

    If partial_output_model is provided, it will be used to update the output model with a submodel for a specific key
    that has to be present in the initial output_model.
    Partial output model is a dictionary with output_key and a schema for the submodel as the value.

    Args:
        output_model (Union[OutputModel, dict, str], optional): Output model. Defaults to None.
        examples (ExampleSelector, optional): Examples. Defaults to None.
        partial_output_model (dict[str, Union[OutputModel, dict, str]], optional): Partial output model. Defaults to None.
    """
    if output_model:
        if isinstance(output_model, dict):
            output_model = OutputModel.from_dict(output_model)
        elif isinstance(output_model, OutputModel) or isinstance(output_model, InputModel):
            return output_model
        elif isinstance(output_model, str):
            output_model = OutputModel.from_string(output_model)


    elif examples:
        if isinstance(examples, list):
            output_model = OutputModel.from_examples(examples)
        else:
            output_model = OutputModel.from_examples(examples.examples)

    else:
        output_model = OutputModel()

    if partial_output_model:
        output_model = add_partial_output_model(output_model, partial_output_model)

    return output_model


def init_input_model(
        input_model: Union[InputModel, dict, str] = None,
        examples: ExampleSelector = None,
        **kwargs
) -> InputModel:
    """Initialize input model from input_model or examples.

    Args:
        input_model (Union[InputModel, dict, str], optional): Input model. Defaults to None.
        examples (ExampleSelector, optional): Examples. Defaults to None.

    """
    if input_model:
        if isinstance(input_model, dict):
            input_model = InputModel.from_dict(input_model)
        elif isinstance(input_model, InputModel):
            return input_model
        elif isinstance(input_model, str):
            input_model = InputModel.from_string(input_model)

    elif examples:
        if isinstance(examples, list):
            input_model = InputModel.from_examples(examples)
        else:
            input_model = InputModel.from_examples(examples.examples)

    else:
        input_model = InputModel()

    return input_model


def load_output_model(sections: dict, examples: ExampleSelector = None, **kwargs):
    if kwargs.get("output_model"):
        output_model = kwargs["output_model"]
        if isinstance(output_model, dict):
            output_model = OutputModel.from_dict(output_model)
        elif isinstance(output_model, OutputModel):
            output_model = output_model

    elif sections.get("output_schema"):
        output_model = OutputModel.from_string(sections["output_schema"])

    elif examples:
        if isinstance(examples, list):
            output_model = OutputModel.from_examples(examples)
        else:
            output_model = OutputModel.from_examples(examples.examples)

    else:
        output_model = OutputModel()

    if kwargs.get("partial_output_model"):
        output_model = add_partial_output_model(output_model, kwargs.get("partial_output_model"))

    return output_model


def load_input_model(sections: dict, examples: ExampleSelector = None, **kwargs):
    """Load input model from sections or examples.

    Args:
        sections (dict): Sections.
        examples (ExampleSelector, optional): Examples. Defaults to None.
    """
    if kwargs.get("input_model"):
        input_model = kwargs["input_model"]
        if isinstance(input_model, dict):
            input_model = InputModel.from_dict(input_model)
        elif isinstance(input_model, OutputModel):
            input_model = input_model

    elif sections.get("input_schema"):
        input_model = InputModel.from_string(sections["input_schema"])

    elif examples:
        if isinstance(examples, list):
            input_model = InputModel.from_examples(examples)
        else:
            input_model = InputModel.from_examples(examples.examples)

    else:
        input_model = InputModel()

    return input_model


def add_partial_output_model(output_model: OutputModel, partial_output_model: dict[str, Union[OutputModel, dict, str]]):
    new_lines = []

    for attr in output_model.lines:
        if attr.key in partial_output_model:
            new_lines.append(attr)
            new_lines.extend(_partial_lines(attr.key, partial_output_model[attr.key]))
        else:
            new_lines.append(attr)
    return OutputModel(lines=new_lines)


def _partial_lines(key: str, partial_schema: str) -> list:
    om = init_output_model(partial_schema)
    lines = []
    for attr in om.lines:
        attr.key = f"{key}.${attr.key}"
        lines.append(attr)
    return lines
