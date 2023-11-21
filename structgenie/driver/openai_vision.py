"""Custom openai driver for structgenie.

using openai 1.2.0 OpenAI() client
"""
import time
from typing import Any, Union, Tuple

import openai

from structgenie.base import BaseGenerationDriver
from structgenie.driver.utils import split_prompt, create_examples_messages, create_chat_message, \
    create_chat_message_with_image, parse_image_path


class OpenAIDriverVision(BaseGenerationDriver):
    """OpenAI Chat Driver

    Utilizes the OpenAI Chat API with structgenie prompt schema.
    """
    prompt: str = None
    model_name: str = None
    llm_kwargs: dict = None

    @classmethod
    def prompt_mode(cls):
        return "chat"

    @classmethod
    def load_driver(
            cls,
            prompt: Union[str, Any],
            model_name: str = "gpt-4-vision-preview",
            llm_kwargs: dict = None,
            **kwargs):
        """Load the driver.

        Args:
            prompt (Union[str, Any]): The prompt.

        Returns:
            OpenAIDriver: The driver.

        """
        cls_ = cls()
        cls_.prompt = prompt
        cls_.model_name = model_name
        cls_.llm_kwargs = llm_kwargs or {}
        return cls_

    def parse_prompt(self, image_path: str = None, **kwargs) -> list[dict]:
        # add inputs to prompt
        prompt = self.prompt.format(**kwargs)

        # split prompt into sections
        system_message = split_prompt(prompt, "system")
        examples = split_prompt(prompt, "examples")
        user_message = split_prompt(prompt, "user")

        # create chat messages
        messages = [create_chat_message("system", system_message)]
        if examples:
            messages.extend(create_examples_messages(examples))

        if image_path:
            messages.append(create_chat_message_with_image(
                "user", user_message, image_url=parse_image_path(image_path))
            )
        else:
            messages.append(create_chat_message("user", user_message))
        return messages

    def completion(self, **kwargs):
        client = openai.OpenAI()
        messages = self.parse_prompt(**kwargs)
        exec_start = time.time()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **self.llm_kwargs
        )

        result = response.choices[0].message.content
        execution_metrics = {
            "execution_time": time.time() - exec_start,
            "token_usage": response.usage.total_tokens,
            "model_name": self.model_name,
            "model_config": self.llm_kwargs,
        }
        return result, execution_metrics

    async def async_completion(self, **kwargs):
        client = openai.AsyncOpenAI()
        messages = self.parse_prompt(**kwargs)
        exec_start = time.time()
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **self.llm_kwargs
        )
        result = response["choices"][0]["message"]
        execution_metrics = {
            "execution_time": time.time() - exec_start,
            "token_usage": response["usage"]["total_tokens"],
            "model_name": self.model_name,
            "model_config": self.llm_kwargs,
        }
        return result, execution_metrics

    def predict(self, **kwargs) -> str:
        """Generate the text.

        Args:
            **kwargs: Keyword arguments for the prompt to pass into placeholder.

        Returns:
            str: The generated text.
        """
        text, _ = self.completion(**kwargs)
        return text

    def predict_and_measure(self, **kwargs) -> Tuple[str, dict]:
        """Generate the text and measure the performance.

        Args:
            **kwargs: Keyword arguments for the prompt to pass into placeholder.

        Returns:
            Tuple[str, dict]: The generated text and the performance metrics.
        """
        text, metrics = self.completion(**kwargs)
        return text, metrics

    async def predict_async(self, **kwargs) -> str:
        """Generate the text.

        Args:
            **kwargs: Keyword arguments for the prompt to pass into placeholder.

        Returns:
            str: The generated text.
        """
        text, _ = await self.async_completion(**kwargs)
        return text

    async def predict_and_measure_async(self, **kwargs) -> Tuple[str, dict]:
        """Generate the text and measure the performance.

        Args:
            **kwargs: Keyword arguments for the prompt to pass into placeholder.

        Returns:
            Tuple[str, dict]: The generated text and the performance metrics.
        """
        text, metrics = await self.async_completion(**kwargs)
        return text, metrics


if __name__ == "__main__":
    pass
