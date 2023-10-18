from structgenie.components.input_output import OutputModel
from structgenie.components.output_parser.fixing import fix_multiline_output, fix_split_output, \
    llm_output_fixing_partial, llm_output_fixing
from structgenie.errors import ParsingPartialError, MultilineParsingError, YamlParsingError
from structgenie.utils.operator.default import parse_default
from structgenie.utils.parsing import parse_yaml_string, format_as_key


class OutputParser:
    """Parse generation output according to the output model into a dict structure."""

    def __init__(self, output_model: OutputModel, fix_by_llm: bool = True, fix_partial_by_llm: bool = True,
                 debug: bool = False):
        self.output_model = output_model
        self.error_log = []
        self.run_metrics = []

        self.fix_by_llm = fix_by_llm
        self.fix_partial_by_llm = fix_partial_by_llm
        self.debug = debug

    def parse(self, text: str, inputs: dict) -> tuple[dict, list, list]:

        output = self.parse_to_dict(text)
        output = self._prefix_output(output)
        output = self._parse_defaults(output, inputs)
        return output, self.run_metrics, self.error_log

    def parse_to_dict(self, text: str) -> dict:
        """Parse the generation text output into a dict structure.

        If yaml parsing fails, try to fix the output with the output fixing parser.
        """
        try:
            return parse_yaml_string(text)
        except Exception as e:
            self._debug("Yaml parsing error", str(e))
            self.error_log.append(YamlParsingError(str(e)))
            return self.fixing_parser(text)

    def fixing_parser(self, text: str) -> dict:
        try:
            return self._fixing_parser(text)
        except Exception as e:
            self._debug("Fixing failed", str(e))
            if self.fix_by_llm:
                self._debug("Fixing failed", "Try LLM parsing")
                output, run_metrics = llm_output_fixing(text, self.output_model, debug=self.debug)
                self.run_metrics.append(run_metrics)
                return output

    def _fixing_parser(self, text: str) -> dict:
        """Run fixing logic to fix parsing error."""

        if any(line.multiline for line in self.output_model.lines):
            self._debug(
                "Multiline", "Try Multiline parsing"
            )
            try:
                return fix_multiline_output(text, self.output_model)
            except MultilineParsingError as e:
                self._debug(
                    "Multiline", str(e)
                )
                self.error_log.append(e)

        output = fix_split_output(text, self.output_model)
        self._debug(
            "Split Partial Parsing",
            "Try Split Partial parsing"
        )

        if any(isinstance(value, ParsingPartialError) for value in output.values()):
            for key, value in output.items():
                if isinstance(value, ParsingPartialError):
                    self._debug(
                        "Split Partial Parsing",
                        f"ParsingPartialError for '{format_as_key(key)}'"
                    )
                    self.error_log.append(value)
                    if self.fix_partial_by_llm:
                        self._debug(
                            "Split Partial Parsing",
                            f"Try LLM Partial parsing for '{format_as_key(key)}'"
                        )
                        _value, _run_metrics = llm_output_fixing_partial(str(value), key, self.output_model,
                                                                         debug=self.debug)
                        self.run_metrics.append(_run_metrics)
                        output[key] = _value[key]
                    else:
                        raise ParsingPartialError(f"Error while parsing output for key '{format_as_key(key)}'.")
        return output

    def _prefix_output(self, output: any) -> dict:
        """Prefix the output with the output prefix if defined."""
        if len(self.output_model.lines) == 1:
            if len(output) > 1 or self.output_model.keys()[0] not in output:
                return {self.output_model.keys()[0]: output}
        return output

    def _parse_defaults(self, output: dict, inputs: dict):
        return parse_default(output, self.output_model, **inputs)

    def _debug(self, step, msg):
        if self.debug:
            print(f"{step}: {msg}")
