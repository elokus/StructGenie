"""A wrapper for making predictions with llm models and libraries with a default yaml parser logic.

YAML format was chosen because it is easy to read and write for humans and machines and uses minimal tokens.

"""
from abc import ABC, abstractmethod
from typing import Union, Any, Optional

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


class BaseOutputAttribute(BaseModel):
    key: str
    type: str = "any"
    rule: Optional[str] = None
    default: Union[str, int, float, bool, list, dict] = None


class BaseOutputModel(BaseModel, ABC):
    attributes: BaseOutputAttribute

    # === class methods ===

    @classmethod
    @abstractmethod
    def from_dict(cls, output_dict: dict):
        pass

    @classmethod
    @abstractmethod
    def from_schema(cls, schema: str):
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
    def output_keys(self) -> list[str]:
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

    @classmethod
    @abstractmethod
    def load_driver(cls, prompt: Union[str, Any], **kwargs):
        pass
