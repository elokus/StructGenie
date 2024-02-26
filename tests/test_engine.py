import pytest

from structgenie.experimental.conditional import ConditionalEngine
from structgenie.pydantic_v1 import BaseModel
from structgenie.components.input_output import OutputModel, InputModel


@pytest.fixture
def output_model_1():
    class Output(BaseModel):
        name: str
        age: str
        country: str

    return OutputModel.from_pydantic(Output)


@pytest.fixture
def output_model_2():
    class Output(BaseModel):
        missing_information: str

    return OutputModel.from_pydantic(Output)


@pytest.fixture
def input_model():
    class Input(BaseModel):
        text: str

    return InputModel.from_pydantic(Input)


@pytest.fixture
def engine(output_model_1, output_model_2, input_model):
    return ConditionalEngine.load_engine(
        instruction="Extract the name, age, and country of a person. If any of the information is missing, return a message indicating the missing information.",
        input_model=input_model,
        output_model=output_model_1,
        output_model_else=output_model_2,
        condition="if name and age and country are present in input",
    )


def test_conditional_engine_if(engine):
    input_data = {"text": "John is 25 years old and lives in the United States."}
    output, _ = engine.run(input_data, raise_error=True)

    assert output == {"name": "John", "age": "25", "country": "United States"}


def test_conditional_engine_else(engine):
    input_data = {"text": "John is 25 years old."}
    output, _ = engine.run(input_data, raise_error=True)

    assert output.get("missing_information") is not None

