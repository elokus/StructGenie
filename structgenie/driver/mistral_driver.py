import time
from typing import Any, Union, Tuple

from mistralai.async_client import MistralAsyncClient
from mistralai.client import MistralClient
from mistralai.client_base import ClientBase
from mistralai.models.chat_completion import ChatMessage

from structgenie.driver.chat_driver import ChatDriver
from structgenie.utils.openai import create_retry_decorator
import os


def clean_output(text: str) -> str:
    """Clean the output from the generation."""
    text = text.replace("\xa0", "_")
    text = text.replace(u"\xa0", u"_")
    text = text.replace("\\_", "_")
    return text


class MistralDriver(ChatDriver):
    """Mistral Chat Driver

    Utilizes the Mistral Chat API with structgenie prompt schema.
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
            model_name: str = "mistral-medium-latest",
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

    @staticmethod
    def _verify_api_key():
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable not set.")
        return api_key

    def _completion(self, client: ClientBase, memory: list[dict] = None, **kwargs):
        messages = self.parse_prompt(memory=memory, **kwargs)
        messages = [ChatMessage(role=m["role"], content=m["content"], name=m.get("name")) for m in messages]

        exec_start = time.time()

        retry_decorator = create_retry_decorator(self)

        @retry_decorator
        def _completion():
            return client.chat(
                model=self.model_name,
                messages=messages,
                **self.llm_kwargs
            )

        response = _completion()

        result = response.choices[0].message.content
        result = clean_output(result)
        execution_metrics = {
            "execution_time": time.time() - exec_start,
            "token_usage": response.usage.total_tokens,
            "model_name": self.model_name,
            "model_config": self.llm_kwargs,
        }
        return result, execution_metrics

    def completion(self, memory: list[dict] = None, **kwargs):
        api_key = self._verify_api_key()
        client = MistralClient(api_key=api_key)
        return self._completion(client, **kwargs)

    async def async_completion(self, memory: list[dict] = None, **kwargs):
        api_key = self._verify_api_key()
        client = MistralAsyncClient(api_key=api_key)
        return self._completion(client, **kwargs)
