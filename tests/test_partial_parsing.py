import pytest

from structgenie.components.input_output import OutputModel
from structgenie.components.output_parser.fixing import fix_split_output
from structgenie.components.output_parser.output_parser import OutputParser


@pytest.fixture
def output():
    return """Reasoning: The input model consists of three keys: 'book_title', 'book_author', and 'release_year'. The values for these keys are expected to be a string, a string, and an integer respectively. The output model is a list of strings, representing the sequels of the book.

Instruction: Extract the sequels of a book given its title, author, and release year."""


@pytest.fixture
def output_model():
    return OutputModel.from_string("Reasoning: <str>\nInstruction: <str>")


def test_partial_parsing(output_model, output):
    parser = OutputParser(output_model=output_model, fix_by_llm=False, fix_partial_by_llm=False, debug=True)
    output, run_metrics, error_log = parser._fixing_parser(output)
    print(output)
    assert all([key in output.keys() for key in ["reasoning", "instruction"]])


def test_partial_parsing(output_model, output):
    text = fix_split_output(output, output_model)
    print(text)
    assert all([key in text.keys() for key in ["reasoning", "instruction"]])


if __name__ == '__main__':
    pytest.main()
