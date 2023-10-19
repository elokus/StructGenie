from typing import Union

from structgenie.base import BaseExampleSelector
from structgenie.components.examples.base import Example
from structgenie.components.examples.load import (
    load_examples_from_string,
    load_examples_from_list,
    load_examples_from_file
)


class ExampleSelector(BaseExampleSelector):
    """Example selector class to select examples from a pool of examples.

    Defining different loading methods for examples as from file, from string, from list.
    """

    example_template: str = "{input}\n---\n{output}"
    example_splitter: str = "===\n"

    examples: list[Example]

    @classmethod
    def load_examples(cls, examples: Union[str, list[Union[Example, str, dict]]]):
        """Load examples from a string, list or file."""
        if not examples:
            return None
        if isinstance(examples, str):
            return cls.from_string(examples)
        elif isinstance(examples, list):
            return cls.from_list(examples)
        else:
            raise ValueError(f"Input type {type(examples)} not supported for loading examples.")

    @classmethod
    def from_string(cls, example_string: str):
        return cls(
            examples=load_examples_from_string(example_string)
        )

    @classmethod
    def from_file(cls, path: str):
        return cls(
            examples=load_examples_from_file(path)
        )

    @classmethod
    def from_list(cls, examples: list[Union[Example, str, dict]]):
        return cls(
            examples=load_examples_from_list(examples)
        )

    def add_example(self, example: Example):
        """Add example to example pool."""
        self.examples.append(example)

    def to_prompt(self, max_token: int = 2000, return_all: bool = False, **kwargs) -> str:
        """Return a prompt string with examples filtered by kwargs.

        Args:
            max_token (int, optional): Max token length of prompt. Defaults to 2000.
            return_all (bool, optional): Return all examples. Defaults to False.
            kwargs: Keyword arguments to filter examples by.

        """
        if return_all:
            return self._examples_to_string(self.examples)

        example_pool = self.filter_examples(**kwargs) if kwargs else self.examples.copy()
        if len(example_pool) == 0:
            return ""

        token_count = 0
        examples = []
        while len(example_pool) > 0:
            next_example = example_pool.pop(0)
            if token_count + next_example.token_count > max_token:
                break
            examples.append(next_example)
            token_count += next_example.token_count

        return self._examples_to_string(examples)

    def filter_examples(self, **kwargs) -> list[Example]:
        """Filter examples based on input kwargs."""
        return [example for example in self.examples if example.filter(**kwargs)]

    def _examples_to_string(self, examples: list[Example]) -> str:
        """Convert list of examples to string."""
        return self.example_splitter.join(
            [example.to_string(template=self.example_template) for example in examples]
        )

    @property
    def input_keys(self):
        return self.examples[0].input_keys

    def __len__(self):
        return len(self.examples)
