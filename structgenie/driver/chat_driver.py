from abc import ABC, abstractmethod
from typing import Any, Union, Tuple

from structgenie.base import BaseGenerationDriver
from structgenie.driver.utils import split_prompt, create_examples_messages, create_chat_message, message_to_str
from structgenie.utils.logging import console_logger as logger


class ChatDriver(BaseGenerationDriver, ABC):
    """Chat Driver

    Utilizes the Chat API with structgenie prompt schema.
    """
    prompt: str = None
    model_name: str = None
    llm_kwargs: dict = None
    max_retries: int = 4
    verbose: int = 0

    @classmethod
    def prompt_mode(cls):
        return "chat"

    def parse_prompt(self, memory: list[dict] = None, **kwargs) -> list[dict]:
        # add inputs to prompt

        if "<%last_output%>" in self.prompt:
            prompt = self.prompt.split("<%last_output%>")[0]
            prompt = prompt.format(**kwargs) + "<%last_output%>" + self.prompt.split("<%last_output%>")[1]
        else:
            prompt = self.prompt.format(**kwargs)


        # split prompt into sections
        system_message = split_prompt(prompt, "system")
        examples = split_prompt(prompt, "examples")
        user_message = split_prompt(prompt, "user")
        last_output = split_prompt(prompt, "last_output")
        user_error = split_prompt(prompt, "user_error")

        # create chat messages
        messages = [create_chat_message("system", system_message)]
        if examples:
            messages.extend(create_examples_messages(examples))
        if memory:
            for message in memory:
                messages.append(create_chat_message(message["role"], message["content"]))

        messages.append(create_chat_message("user", user_message))
        if last_output and user_error:
            messages.append(create_chat_message("assistant", last_output))
            messages.append(create_chat_message("user", user_error))

        if self.verbose >= 3:
            msgs = "\n".join([message_to_str(m) for m in messages])
            logger.debug(f"messages:\n{msgs}")

        return messages

    @abstractmethod
    def completion(self, memory: list[dict] = None, **kwargs):
        pass

    @abstractmethod
    async def async_completion(self, memory: list[dict] = None, **kwargs):
        pass

    def predict(self, memory: list[dict] = None, **kwargs) -> str:
        """Generate the text.

        Args:
            memory (list[dict], optional): The memory. Defaults to None.
            **kwargs: Keyword arguments for the prompt to pass into placeholder.

        Returns:
            str: The generated text.
        """
        text, _ = self.completion(**kwargs)
        return text

    def predict_and_measure(self, memory: list[dict] = None, **kwargs) -> Tuple[str, dict]:
        """Generate the text and measure the performance.

        Args:
            memory (list[dict], optional): The memory. Defaults to None.
            **kwargs: Keyword arguments for the prompt to pass into placeholder.

        Returns:
            Tuple[str, dict]: The generated text and the performance metrics.
        """
        text, metrics = self.completion(**kwargs)
        return text, metrics

    async def predict_async(self, memory: list[dict] = None, **kwargs) -> str:
        """Generate the text.

        Args:
            memory (list[dict], optional): The memory. Defaults to None.
            **kwargs: Keyword arguments for the prompt to pass into placeholder.

        Returns:
            str: The generated text.
        """
        text, _ = await self.async_completion(**kwargs)
        return text

    async def predict_and_measure_async(self, memory: list[dict] = None, **kwargs) -> Tuple[str, dict]:
        """Generate the text and measure the performance.

        Args:
            memory (list[dict], optional): The memory. Defaults to None.
            **kwargs: Keyword arguments for the prompt to pass into placeholder.

        Returns:
            Tuple[str, dict]: The generated text and the performance metrics.
        """
        text, metrics = await self.async_completion(**kwargs)
        return text, metrics
