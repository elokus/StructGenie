from unittest.mock import Mock

import pytest

from structgenie.engine import StructEngine
from structgenie.errors import MaxRetriesError


@pytest.fixture
def template():
    return """Reverse engineer the instruction of a task with following input and output models.

# Input
Input Model: {inp_model}
Output Model: {out_model}
---
Reasoning: <str>
Instruction: <str>
"""


@pytest.fixture
def mock_structengine(mocker):
    mock = Mock(spec=StructEngine.from_template(template))
    mocker.patch('structgenie.engine.StructEngine._call_executor', side_effect=[
        ("Reasoning: I knew it all along.\n", {}),
        ("Reasoning: I knew it all along.\nConstrcution: Do it again.", {}),
        ("Reasoning: I knew it all along.\nInstruction: Do it again.", {})])
    return mock


def test_failure_rate(mocker, template):
    # mock_structengine._call_executor.return_value = ("Reasoning: I knew it all along.\nInstruction: Do it again.", {})
    mocker.patch(
        'structgenie.engine.StructEngine._call_executor',
        side_effect=[
            ("Reasoning: I knew it all along.\n", {"model_name": "some model"}),
            ("Reasoning: I knew it all along.\nConstrcution: Do it again.", {"model_name": "some model"}),
            ("Reasoning: I knew it all along.\nInstruction: Do it again.", {"model_name": "some model"})
        ]
    )

    engine = StructEngine.from_template(template)
    output, m = engine.run(inputs={"input_model": "some model", "output_model": "some model"})

    assert output == {"reasoning": "I knew it all along.", "instruction": "Do it again."}
    assert m["failure_rate"] == 2
    assert engine.num_metrics_logged == 3


def test_max_retries(mocker, template):
    # mock_structengine._call_executor.return_value = ("Reasoning: I knew it all along.\nInstruction: Do it again.", {})
    mocker.patch(
        'structgenie.engine.StructEngine._call_executor',
        side_effect=[
            ("Reasoning: I knew it all along.\n", {"model_name": "some model"}),
            ("Reasoning: I knew it all along.\n", {"model_name": "some model"}),
            ("Reasoning: I knew it all along.\nConstrcution: Do it again.", {"model_name": "some model"}),
            ("Reasoning: I knew it all along.\nInstruction: Do it again.", {"model_name": "some model"})
        ]
    )

    engine = StructEngine.from_template(template)
    engine.max_retries = 2
    error = None
    try:
        output, m = engine.run(inputs={"input_model": "some model", "output_model": "some model"})
        print(output, m)
    except Exception as e:
        error = e

    print(error)

    assert isinstance(error, MaxRetriesError)
