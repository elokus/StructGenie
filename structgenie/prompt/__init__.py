from abc import ABC, abstractmethod


class BasePromptBuilder(ABC):
    """Base class for prompt builders."""

    @abstractmethod
    def build(self) -> str:
        """Build the prompt.

        Returns:
            str: The prompt.
        """
        pass
