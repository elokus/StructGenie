"""Custom openai driver for structgenie.

using openai 1.2.0 OpenAI() client
"""
import re
import time
from typing import Any, List, Union, Tuple

import openai

from structgenie.base import BaseGenerationDriver


def split_prompt(prompt: str, tag: str) -> Union[str, None]:
    """Split prompt into sections.

    Args:
        prompt (str): The prompt.

    Returns:
        List[str]: The sections.

    """
    # get pattern <%tag%> ... </%tag%>
    try:
        pattern = re.compile(rf"<%{tag}%>(.*?)</%{tag}%>", re.DOTALL)
        section = re.findall(pattern, prompt)
        return section[0].strip()
    except:
        return None


def create_examples_messages(examples: str) -> List[dict]:
    """Returns a list of chat messages from examples."""
    messages = []
    examples = examples.split("\n===\n")
    for example in examples:
        user, assistant = example.split("\n---\n")
        messages.append(create_chat_message("user", user.strip(), name="example_user"))
        messages.append(create_chat_message("assistant", assistant.strip(), name="example_assistant"))
    return messages


def create_chat_message(role: str, content: str, name: str = None) -> dict:
    """Returns a dict representing a chat message."""
    if name:
        return {"role": role, "name": name, "content": content}
    return {"role": role, "content": content}


class OpenAIDriver(BaseGenerationDriver):
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
            model_name: str = "gpt-3.5-turbo",
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

    def parse_prompt(self, **kwargs) -> list[dict]:
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
