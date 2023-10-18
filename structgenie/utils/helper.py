def count_tokens(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    import tiktoken
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def remove_reasoning(data: dict):
    for key in ["reason", "chain-of-thoughts", "reasoning"]:
        if key in data:
            del data[key]
    return data
