import pytest
from pydantic import BaseModel, Field

from structgenie.components.input_output import OutputModel
from structgenie.components.validation.validator import Validator
from structgenie.errors import ValidationKeyError, ValidationTypeError, ValidatorExecutionError


@pytest.fixture()
def output_model_simple():
    class Output(BaseModel):
        reasoning: str
        result: str
        meta: dict

    return OutputModel.from_pydantic(Output)


@pytest.fixture()
def output_model_nested():
    class Member(BaseModel):
        name: str
        role: str
        age: int

    class Output(BaseModel):
        family_name: str
        family_members: dict[str, Member] = Field(rule="for each $role in ['father', 'mother', 'son']")

    return OutputModel.from_pydantic(Output)


@pytest.fixture()
def output_model_nested_list():
    class Member(BaseModel):
        name: str
        role: str
        age: int

    class Output(BaseModel):
        family_name: str
        family_members: list[dict[str, Member]] = Field(rule="for each $role in ['father', 'mother', 'son']")

    return OutputModel.from_pydantic(Output)


def test_validator_key_error(output_model_simple):
    output = {"reasoning": "I am a robot", "result": "I am a string"}
    validator = Validator.from_output_model(output_model_simple)
    errors = validator.validate(output, {})
    assert not isinstance(errors[0], ValidatorExecutionError)
    assert any([isinstance(error, ValidationKeyError) for error in errors])


def test_validator_type_error(output_model_simple):
    output = {"reasoning": "I am a robot", "result": 1, "meta": "I am a string"}
    validator = Validator.from_output_model(output_model_simple)
    errors = validator.validate(output, {})
    assert any([isinstance(error, ValidationTypeError) for error in errors])


def test_validator_nested(output_model_nested):
    output = {"family_name": "Smith", "family_members": {
        "father": {"name": "John", "role": "father", "age": 45},
        "mother": {"name": "Jane", "role": "mother", "age": 42},
        "son": {"name": "Jack", "role": "son", "age": 18}
    }}
    validator = Validator.from_output_model(output_model_nested)
    errors = validator.validate(output, {})
    print(errors)
    assert not errors


def test_validator_nested_error(output_model_nested):
    output = {"family_name": "Smith", "family_members": {
        "father": {"name": "John", "role": "father", "age": 45},
        "mother": {"name": "Jane", "role": "mother", "age": 42},
    }}
    validator = Validator.from_output_model(output_model_nested)
    errors = validator.validate(output, {})

    assert any([isinstance(error, ValidationKeyError) for error in errors])


def test_validator_nested_list(output_model_nested_list):
    output = {"family_name": "Smith", "family_members": [
        {"father": {"name": "John", "role": "father", "age": 45}},
        {"mother": {"name": "Jane", "role": "mother", "age": 42}},
        {"son": {"name": "Jack", "role": "son", "age": 18}}
    ]}
    validator = Validator.from_output_model(output_model_nested_list)
    errors = validator.validate(output, {})
    assert not errors


def test_validator_nested_list_error(output_model_nested_list):
    output = {"family_name": "Smith", "family_members": [
        {"father": {"name": "John", "role": "father", "age": 45}},
        {"mother": {"name": "Jane", "role": "mother", "age": 42}},
        {"son": {"name": "Jack", "role": "son"}}
    ]}
    validator = Validator.from_output_model(output_model_nested_list)
    errors = validator.validate(output, {})
    assert any([isinstance(error, ValidationKeyError) for error in errors])


if __name__ == '__main__':
    pytest.main()
