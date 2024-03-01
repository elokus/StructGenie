"""Custom openai driver for structgenie.

using openai 1.2.0 OpenAI() client
"""
import time
from typing import Any, Union, Tuple

import openai

from structgenie.driver.chat_driver import ChatDriver
from structgenie.driver.utils import split_prompt, create_examples_messages, create_chat_message, message_to_str
from structgenie.utils.openai import create_retry_decorator
from structgenie.utils.logging import console_logger as logger


class OpenAIDriver(ChatDriver):
    """OpenAI Chat Driver

    Utilizes the OpenAI Chat API with structgenie prompt schema.
    """
    prompt: str = None
    model_name: str = None
    llm_kwargs: dict = None
    max_retries: int = 4
    verbose: int = 0

    @classmethod
    def prompt_mode(cls):
        return "chat"

    @classmethod
    def load_driver(
            cls,
            prompt: Union[str, Any],
            model_name: str = "gpt-3.5-turbo",
            llm_kwargs: dict = None,
            **kwargs):
        """Load the driver.

        Args:
            prompt (Union[str, Any]): The prompt.
            model_name (str, optional): The model name. Defaults to "gpt-3.5-turbo".
            llm_kwargs (dict, optional): The model config. Defaults to None.

        Returns:
            OpenAIDriver: The driver.

        """
        cls_ = cls()
        cls_.prompt = prompt
        cls_.model_name = model_name
        cls_.llm_kwargs = llm_kwargs or {}
        return cls_

    def completion(self, memory: list[dict] = None, **kwargs):
        client = openai.OpenAI()
        messages = self.parse_prompt(memory=memory, **kwargs)
        exec_start = time.time()

        retry_decorator = create_retry_decorator(self)

        @retry_decorator
        def _completion():
            return client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **self.llm_kwargs
            )

        response = _completion()

        result = response.choices[0].message.content
        execution_metrics = {
            "execution_time": time.time() - exec_start,
            "token_usage": response.usage.total_tokens,
            "model_name": self.model_name,
            "model_config": self.llm_kwargs,
        }
        return result, execution_metrics

    async def async_completion(self, memory: list[dict] = None, **kwargs):
        client = openai.AsyncOpenAI()
        messages = self.parse_prompt(memory=memory, **kwargs)
        exec_start = time.time()

        retry_decorator = create_retry_decorator(self)

        @retry_decorator
        async def _completion():
            return await client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **self.llm_kwargs
            )

        response = await _completion()
        result = response.choices[0].message.content
        execution_metrics = {
            "execution_time": time.time() - exec_start,
            "token_usage": response.usage.total_tokens,
            "model_name": self.model_name,
            "model_config": self.llm_kwargs,
        }
        return result, execution_metrics


if __name__ == "__main__":
    pass
