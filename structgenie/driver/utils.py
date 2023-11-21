import base64
import os
import re
from typing import Any, Dict, Optional, Union, List

import tiktoken


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0613":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
  See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")


def create_chat_message(role: str, content: str, name: str = None) -> dict:
    """Returns a dict representing a chat message."""
    if name:
        return {"role": role, "name": name, "content": content}
    return {"role": role, "content": content}


def create_chat_message_with_image(
        role: str,
        content: str,
        image_url: str = None,
        name: str = None) -> dict:
    """Returns a dict representing a chat message."""

    if not content:
        content = "follow the instruction for this image"

    msg = {"role": role,
           "content": [
               {"type": "text", "text": content},
               {"type": "image_url", "image_url": {"url": image_url}}
           ]
           }

    if name:
        msg["name"] = name
    return msg


def parse_image_path(image_url: str) -> str:
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    if image_url.startswith("http"):
        return image_url
    elif os.path.exists(image_url):
        return f"data:image/jpeg;base64,{encode_image(image_url)}"
    else:
        raise ValueError(f"Image path {image_url} not found.")





def parse_completion(completion) -> tuple[str, dict]:
    """Returns a dict representing a chat message.

    Example:
    >>> completion = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-3.5-turbo-0613",
        "system_fingerprint": "fp_44709d6fcb",
        "choices": [{
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "\n\nHello there, how may I assist you today?",
        },
        "finish_reason": "stop"
        }],
        "usage": {
        "prompt_tokens": 9,
        "completion_tokens": 12,
        "total_tokens": 21
        }
        }
    >>> parse_completion(completion)
    >>> ('Hello there, how may I assist you today?', {'prompt_tokens': 9, 'completion_tokens': 12, 'total_tokens': 21})
    """
    message = completion["choices"][0]["message"]
    usage = completion["usage"]
    return message["content"], usage


def get_from_dict_or_env(
        data: Dict[str, Any], key: str, env_key: str, default: Optional[str] = None
) -> str:
    """Get a value from a dictionary or an environment variable."""
    if key in data and data[key]:
        return data[key]
    else:
        return get_from_env(key, env_key, default=default)


def get_from_env(key: str, env_key: str, default: Optional[str] = None) -> str:
    """Get a value from a dictionary or an environment variable."""
    if env_key in os.environ and os.environ[env_key]:
        return os.environ[env_key]
    elif default is not None:
        return default
    else:
        raise ValueError(
            f"Did not find {key}, please add an environment variable"
            f" `{env_key}` which contains it, or pass"
            f"  `{key}` as a named parameter."
        )


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
