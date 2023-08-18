from typing import Union

from structgenie.examples import ExampleSelector
from structgenie.input_output import OutputModel


def init_output_model(
        output_model: Union[OutputModel, dict, str] = None,
        examples: ExampleSelector = None,
        **kwargs
) -> OutputModel:
    if output_model:
        if isinstance(output_model, dict):
            return OutputModel.from_dict(output_model)
        elif isinstance(output_model, OutputModel):
            return output_model
        elif isinstance(output_model, str):
            return OutputModel.from_schema(output_model)

    elif examples:
        return OutputModel.from_examples(examples)

    return OutputModel()


def load_output_model(sections: dict, examples: ExampleSelector = None, **kwargs):
    if kwargs.get("output_model"):
        output_model = kwargs["output_model"]
        if isinstance(output_model, dict):
            return OutputModel.from_dict(output_model)
        elif isinstance(output_model, OutputModel):
            return output_model

    if sections.get("output_schema"):
        return OutputModel.from_schema(sections["output_schema"])

    if examples:
        return OutputModel.from_examples(examples)

    return OutputModel()
