

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


def build_prompt_from_template(template, chat_mode: bool = False, **kwargs):
    from structgenie.components.examples import ExampleSelector
    from structgenie.components.input_output import load_output_model, load_input_model
    from structgenie.utils.templates import extract_sections
    from structgenie.components.prompt.builder import PromptBuilder

    sections = extract_sections(template.strip())

    instruction = sections.get("instruction")
    examples = ExampleSelector.load_examples(sections.get("examples"))
    output_model = load_output_model(
        sections, examples
    )
    input_model = load_input_model(sections, examples)

    prompt_builder = PromptBuilder(
        instruction=instruction,
        examples=examples,
        output_model=output_model,
        input_model=input_model,
        **kwargs
    )
    return prompt_builder.build(chat_mode=chat_mode)
