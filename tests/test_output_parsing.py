import dotenv
import pytest
from pydantic import BaseModel

from structgenie.components.input_output import OutputModel
from structgenie.components.output_parser.fixing import fix_split_output
from structgenie.components.output_parser.output_parser import OutputParser


@pytest.fixture()
def generated_text():
    return """
Reasoning: The input is a valid SMILES string. Meta: values according to something else
Result: The input is a valid SMILES string.
Meta:
    Key: value
    Key2: value2"""


@pytest.fixture()
def generated_text_with_llm_error():
    return """
Reasoning: The input is a valid SMILES string. Meta: values according to something else
Result: The input is a valid SMILES string.
Meta:
    Key: value
    Key2: value2  
Some other text that should be ignored
"""


@pytest.fixture()
def test_output_model():
    class Output(BaseModel):
        reasoning: str
        result: str
        meta: dict

    return OutputModel.from_pydantic(Output)


def test_fix_split_output(generated_text, test_output_model):
    output = fix_split_output(generated_text, test_output_model)
    assert output == {
        "reasoning": "The input is a valid SMILES string. Meta: values according to something else",
        "result": "The input is a valid SMILES string.",
        "meta": {"key": "value", "key2": "value2"},
    }

def test_output_parser(generated_text, test_output_model):
    parser = OutputParser(test_output_model)
    output, run_metrics, error_log = parser.parse(generated_text, {})
    assert output == {
        "reasoning": "The input is a valid SMILES string. Meta: values according to something else",
        "result": "The input is a valid SMILES string.",
        "meta": {"key": "value", "key2": "value2"},
    }
    assert run_metrics == []
    assert len(error_log) == 0


def test_output_parser_with_llm(generated_text_with_llm_error, test_output_model):
    dotenv.load_dotenv()
    parser = OutputParser(test_output_model)
    output, run_metrics, error_log = parser.parse(generated_text_with_llm_error, {})
    assert output == {
        "reasoning": "The input is a valid SMILES string. Meta: values according to something else",
        "result": "The input is a valid SMILES string.",
        "meta": {"key": "value", "key2": "value2"},
    }
    assert len(run_metrics) >= 1
    assert len(error_log) >= 1


def test_output_parser_duplicate_keys():
    output = """
    Reasoning: The input is a valid SMILES string. Reasoning: values according to something else
    Result: The input is a valid SMILES string.
    ```yaml
    Reasoning: The input is a valid SMILES string from below. values according to something else
    Result: The input is a valid SMILES string.
    ```"""
    output_model = OutputModel.from_string("Reasoning: <str>\nResult: <str>")
    parser = OutputParser(output_model)
    output, run_metrics, error_log = parser.parse(output, {})

    print(output)
    assert error_log == []


def test_output_parser_duplicate_keys():
    output = """
Reasoning: The input is a valid SMILES string. Reasoning: values according to something else
Result: The input is a valid SMILES string.
"""
    output_model = OutputModel.from_string("Reasoning: <str>\nResult: <str>")
    parser = OutputParser(output_model)
    output, run_metrics, error_log = parser.parse(output, {})

    print(output)
    assert error_log == []



if __name__ == '__main__':
    pytest.main()
