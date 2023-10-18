from structgenie.components.examples.base import Example
from structgenie.utils.parsing._template_decomposer import extract_examples_content, extract_system_instruction
from structgenie.utils.templates import extract_section
from structgenie.utils.templates.load_functions import load_and_call_system_function
from structgenie.utils.templates.section_tags import section_in_string


def load_examples_from_file(path: str) -> list[Example]:
    """Load examples from file"""
    with open(path, "r") as file:
        return load_examples_from_string(file.read())


def load_examples_from_string(string: str, splitter: str = "==="):
    """Load examples from a string"""

    # isolate example string
    if section_in_string(string, "examples"):
        example_string = extract_section(string, "examples")
    else:
        example_string = string

    example_content = extract_examples_content(example_string) or example_string
    system_instruction = extract_system_instruction(example_string)
    if system_instruction:
        example_content = load_and_call_system_function(system_instruction)

    return [Example.from_string(example) for example in example_content.split(splitter)]


def load_examples_from_list(examples: list) -> list[Example]:
    """Load examples from a list"""
    if len(examples) > 0:
        if isinstance(examples[0], Example):
            return examples
        elif isinstance(examples[0], str):
            return [Example.from_string(example) for example in examples]
        elif isinstance(examples[0], dict):
            return [Example.from_dict(example) for example in examples]

        raise ValueError(
            f"Input type {type(examples[0])} not supported for loading examples."
        )
    raise ValueError("Example input list is empty.")
