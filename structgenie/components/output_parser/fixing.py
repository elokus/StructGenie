import re

from structgenie.components.input_output import OutputModel
from structgenie.errors import ParsingPartialError, ParsingFixingError, MultilineParsingError
from structgenie.utils.parsing import parse_multi_line_string, format_as_key, parse_yaml_string


def fix_multiline_output(text: str, output_model) -> dict:
    """Fix multiline output."""
    if any(line.multiline for line in output_model.lines):

        idx_keys = [(i, line.key) for i, line in enumerate(output_model.lines) if line.multiline]
        key_pairs = []
        for idx, key in idx_keys:
            next_key = output_model.lines[idx + 1].key if idx + 1 < len(output_model.lines) else None
            key_pairs.append((key, next_key))
        try:
            return parse_multi_line_string(text, key_pairs, idx_keys)
        except Exception as e:
            raise MultilineParsingError(f"Failed Multiline parsing: {e}")


def fix_split_output(text: str, output_model: OutputModel) -> dict:
    """Split the generated output by their keys and try to parse them separately."""

    # map output to keys
    key_types = [(line.key, line.type) for line in output_model.lines if "." not in line.key]
    formatted_keys = [f"{format_as_key(key)}:" for key, _ in key_types]
    key_split_pattern = [f"\n{key}" for key in formatted_keys]
    key_split_pattern.extend([f"^{key}" for key in formatted_keys])

    # split output by keys
    text_parts = re.split(r"(\n{})".format("|".join(key_split_pattern)), text)

    # parse parts
    output = {}
    for i, part in enumerate(text_parts):
        if part.strip() in formatted_keys:
            key, type_ = key_types[formatted_keys.index(part.strip())]
            value = text_parts[i + 1] if i + 1 < len(text_parts) else None

            if type_ == "str" or type_ == "multiline":
                output[key] = value.strip()

            else:
                try:
                    output[key] = parse_yaml_string(part + value)[key]
                except Exception as e:
                    output[key] = ParsingPartialError(
                        f"Error while parsing output for key '{format_as_key(key)}'."
                        f"Output: {part + value}"
                    )
    return output


# TODO: add logic for passing run_metrics to calling engine
def llm_output_fixing_partial(error_msg: str, key: str, output_model: OutputModel, debug: bool = False) -> dict:
    from structgenie.engine import StructEngine

    partial_output_model = OutputModel(lines=[
        line for line in output_model.lines if line.key == key or line.key.startswith(f"{key}.")
    ])

    engine = StructEngine.from_defaults("fix_partial_parsing", output_model=partial_output_model, debug=debug)
    engine.fix_parsing_by_llm = False
    engine.return_metrics = True
    try:
        return engine.run(inputs=dict(error_msg=error_msg))
    except Exception as e:
        raise ParsingFixingError(f"Error while fixing partial parsing error for key '{key}'. Error: {e}")


def llm_output_fixing(text: str, output_model: OutputModel, debug: bool = False) -> dict:
    from structgenie.engine import StructEngine

    fixing_engine = StructEngine.from_defaults("fix_parsing_error", output_model=output_model, debug=debug)
    fixing_engine.fix_parsing_by_llm = False
    fixing_engine.return_metrics = True

    try:
        return fixing_engine.run(inputs=dict(last_output=text))
    except Exception as e:
        raise ParsingFixingError(f"Error while fixing parsing by llm error: {e}")
