"""A wrapper for making predictions with llm models and libraries with a default yaml parser logic.

YAML format was chosen because it is easy to read and write for humans and machines and uses minimal tokens.

"""
from abc import ABC, abstractmethod
from typing import Union, Any, Optional, Tuple

from pydantic import BaseModel


class BaseExampleSelector(BaseModel, ABC):
    """Interface for selecting examples to include in prompts."""

    @abstractmethod
    def add_example(self, *args, **kwargs) -> any:
        """Add new example to store for a key."""

    @abstractmethod
    def to_prompt(self, max_token: int = 2000, **kwargs) -> list[dict]:
        """Select which examples to use based on the inputs."""

    @property
    @abstractmethod
    def input_keys(self):
        pass


class BaseIOLine(BaseModel):
    key: str
    type: str = "any"
    rule: Optional[str] = None
    options: Optional[list] = None
    multiple_select: bool = False
    default: Union[str, int, float, bool, list, dict] = None


class BaseIOModel(BaseModel, ABC):
    lines: list[BaseIOLine]

    # === class methods ===

    @classmethod
    @abstractmethod
    def from_dict(cls, output_dict: dict):
        pass

    @classmethod
    @abstractmethod
    def from_string(cls, schema: str):
        pass

    @classmethod
    @abstractmethod
    def from_examples(cls, examples: BaseExampleSelector):
        pass

    # === properties ===

    @property
    @abstractmethod
    def as_dict(self):
        pass

    @property
    @abstractmethod
    def prompt_schema(self) -> str:
        pass

    @property
    @abstractmethod
    def template_schema(self) -> str:
        pass

    @property
    @abstractmethod
    def defaults(self):
        pass

    # === getters ===

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def get_nested_dict(self, key: str, full_key: bool = True) -> dict:
        pass

    @abstractmethod
    def get_nested_attr(self, key: str, exclude_parent: bool = True) -> dict:
        pass

    @abstractmethod
    def get_default(self, key: str, **kwargs):
        pass

    def __len__(self):
        return len(self.lines)

    @abstractmethod
    def dump_to_prompt(self, param, **kwargs):
        pass


class BaseEngine(BaseModel, ABC):
    """Base class for prediction engines"""

    @classmethod
    @abstractmethod
    def from_template(
            cls,
            **kwargs):
        """Build Prediction Engine from template."""
        pass

    @classmethod
    @abstractmethod
    def from_instruction(
            cls,
            **kwargs):
        """Build Prediction Engine from instruction."""
        pass

    @classmethod
    @abstractmethod
    def load_engine(
            cls,
            **kwargs):
        """Load the engine."""
        pass

    @abstractmethod
    def run(self, inputs: dict, **kwargs):
        pass


class BasePromptBuilder(ABC):
    """Base class for prompt builders."""

    examples: Union[str, BaseExampleSelector] = None

    @abstractmethod
    def build(self, **kwargs) -> str:
        """Build the prompt.

        Returns:
            str: The prompt.
        """
        pass

    @abstractmethod
    def fix_parsing(self, error: str, **kwargs):
        pass

    @abstractmethod
    def fix_validation(self, error: str, **kwargs):
        pass

    @staticmethod
    def get_input_variables(prompt: str):
        import re
        return re.findall(r"\{(\w+)\}", prompt)

    @property
    def has_examples(self):
        return self.examples is not None


class BaseValidator(ABC):
    """Validate an output based on a key and a set of rules.

    Takes the valid values from one input key and validates the output based on those values.
    """

    @abstractmethod
    def validate(self, output: Union[str, dict], inputs: dict) -> Union[str, None]:
        pass


class BaseGenerationDriver(ABC):

    @abstractmethod
    def predict(self, **kwargs) -> str:
        """Generate the text.

        Returns:
            str: The generated text.
        """
        pass

    @abstractmethod
    def predict_and_measure(self, **kwargs) -> Tuple[str, dict]:
        """Generate the text and measure the performance.

        Returns:
            Tuple[str, dict]: The generated text and the performance metrics.
        """
        pass

    @abstractmethod
    async def predict_async(self, **kwargs) -> str:
        """Generate the text. (async)"""
        pass

    @abstractmethod
    async def predict_and_measure_async(self, **kwargs) -> Tuple[str, dict]:
        """Generate the text and measure the performance.

        Returns:
            Tuple[str, dict]: The generated text and the performance metrics.
        """
        pass

    @classmethod
    @abstractmethod
    def load_driver(cls, prompt: Union[str, Any], **kwargs):
        pass


class BaseExample(BaseModel, ABC):
    input: dict
    output: dict
    _template: str = "{input}---\n{output}"

    @abstractmethod
    def __str__(self):
        pass

    @classmethod
    @abstractmethod
    def from_string(cls, text: str):
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, example_dict: dict):
        pass

    @abstractmethod
    def filter(self, **kwargs) -> bool:
        """Filter example based on input kwargs."""
        return True

    @property
    def token_count(self) -> int:
        """Return the total number of tokens in the input and output."""
        from structgenie.utils import count_tokens
        return count_tokens(str(self))

    @property
    def input_keys(self):
        return list(self.input.keys())

    @property
    def output_keys(self):
        return list(self.output.keys())

    @property
    @abstractmethod
    def output_types(self):
        pass

    @property
    @abstractmethod
    def input_types(self):
        pass
