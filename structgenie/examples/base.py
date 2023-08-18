from abc import ABC, abstractmethod
from typing import Any, List

from pydantic import BaseModel, validator

from structgenie.base import BaseExampleSelector
from structgenie.parser import dump_to_yaml_string, parse_yaml_string, get_type_dict_from_object


class Example(BaseModel):
    input: dict
    output: dict
    _template: str = "{input}---\n{output}"

    def __str__(self):
        return self._template.format(
            input=dump_to_yaml_string(self.input), output=dump_to_yaml_string(self.output)
        )

    @validator("input", "output", pre=True)
    def _parse_yaml(cls, v):
        if isinstance(v, str):
            return parse_yaml_string(v)
        return v

    @classmethod
    def from_string(cls, text: str):
        """Load Example from string.

        Example:
             >> text = '''
            ... Age: 20
            ... Height: 172
            ... Weight: 150
            ... ---
            ... BMI: 20'''
             >> print(Example.from_string(text))
            ... Example(input={'age': 20, 'height': 172, 'weight': 150}, output={'bmi': 20})

        """
        inputs, outputs = text.split("---")
        return Example(input=parse_yaml_string(inputs), output=parse_yaml_string(outputs))

    @classmethod
    def from_dict(cls, example_dict: dict):
        return cls(**example_dict)

    def output_dict(self):
        """Return output as a dictionary with dot notation of nested objects."""
        return get_type_dict_from_object(self.output)

    def filter(self, **kwargs) -> bool:
        """Filter example based on input kwargs."""
        for key, value in kwargs.items():
            if self.input.get(key) != value:
                return False
        return True

    @property
    def token_count(self) -> int:
        """Return the total number of tokens in the input and output."""
        from structgenie.utils import count_tokens
        return count_tokens(str(self))

    @property
    def input_keys(self):
        return list(self.input.keys())
