import pytest

from structgenie.engine import StructEngine


@pytest.fixture()
def family_loop_template():
    return """
Generate a Person for each of the following family roles:
{family_roles}

Begin!
Family Members: {family_roles}
---
Family: <list[dict], rule=for each $role in ['father', 'mother', 'son']>
Family.$role: <dict>
Family.$role.name: <str>
Family.$role.age: <int>
"""


@pytest.fixture()
def family_input():
    return {
        "family_roles": ["father", "mother", "son", "daughter"]
    }


def test_for_loop(family_loop_template, family_input):
    engine = StructEngine.from_template(family_loop_template)
    output, run_metrics = engine.run(family_input)

    assert all([key in family_input["family_roles"] for key in output["family"].keys()])


if __name__ == '__main__':
    pytest.main()
