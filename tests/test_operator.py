from typing import Literal, Any, Union

import pytest

from structgenie.engine.conditional import ConditionalEngine
from structgenie.pydantic_v1 import BaseModel
from structgenie.components.input_output import OutputModel, InputModel


@pytest.fixture
def output_model_1():
    class WhereStatement(BaseModel):
        column: str
        operator: Literal['==', '>', '<', '>=', '<=', '!=']
        value: Any

    class QueryConfig(BaseModel):
        table_name: str
        where_statements: list[Union[WhereStatement, None]]
    print("Before output model creation")
    return OutputModel.from_pydantic(QueryConfig)


@pytest.fixture
def output_model_2():
    class Output(BaseModel):
        missing_information: str

    return OutputModel.from_pydantic(Output)


@pytest.fixture
def input_model():
    class Input(BaseModel):
        text: str
        table_name: str
        orm_model: str
    print("Before input model creation")
    return InputModel.from_pydantic(Input)


@pytest.fixture
def engine(output_model_1, output_model_2, input_model):
    print("Before engine creation")
    return ConditionalEngine.load_engine(
        instruction=("From the text input provided extract all necessary information to query a table in the database. "
                     "If the input text is not sufficient to query a table in the database, return a message indicating what information is missing."),
        input_model=input_model,
        output_model=output_model_1,
        output_model_else=output_model_2,
        condition="All necessary and none optional information is present in the input text",
    )


def test_conditional_engine_if(engine):
    text =  "Please find me all revenues between 24th August 2022 and 1st December 2022"
    orm_model = "id = <Optional>, description = <str>, net_amount = <float>, gross_amount = <float>, tax_rate = <float>, date = <datetime>"
    table_name = "RevenueData"

    input_data = {"text": text, "table_name": table_name, "orm_model": orm_model}
    output, _ = engine.run(input_data, raise_error=True)

    print(output)
    assert output.get("missing_information") is None

