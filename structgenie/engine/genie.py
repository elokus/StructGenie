from structgenie.base import BaseGenerationDriver
from structgenie.components.output_parser.output_parser import OutputParser
from structgenie.engine.base import BaseEngine
from structgenie.errors import ParsingError, ValidationError, EngineRunError, MaxRetriesError
from structgenie.utils.parsing import (
    dump_to_yaml_string,
    format_inputs,
    prepare_inputs_placeholders
)


# TODO: define blocked input keys: error_msg, error, input, input_schema, input_model, output_schema, output_model

class StructEngine(BaseEngine):

    # === Run ===

    def run(self, inputs: dict, raise_error: bool = False, **kwargs):
        """Run the chain.

        Args:
            inputs (dict): The inputs for the chain.
            **kwargs: Keyword arguments for the chain.

        Returns:
            Output (any): The output of the chain.
            (optional) Output (dict), run_metrics (dict): The output of the chain and the run metrics.

        """
        self.last_error = None
        error_index = 0

        n_run = 0
        while n_run <= self.max_retries:
            try:
                output = self._run(inputs, error_msg=self.last_error, **kwargs)
                if self.return_metrics:
                    return output, self.run_metrics
                return output

            except Exception as e:
                if raise_error or self.raise_errors:
                    raise e
                e = EngineRunError(f"run_num: {n_run}/{self.max_retries} ", e)
                self._log_error(e)

                # prepare error remarks
                if len(self.run_metrics["errors"]) > error_index:
                    new_errors = [er for er in self.run_metrics["errors"][error_index:]]
                    prompt_errors = [
                        str(er) for er in new_errors if isinstance(er, ParsingError) or isinstance(er, ValidationError)
                    ]
                    error_index = len(self.run_metrics["errors"])
                    self.last_error = "\n - ".join(prompt_errors)

                self._debug(
                    f"Run Error #{n_run}/{self.max_retries}",
                    raised=str(e),
                )
                n_run += 1

        e = MaxRetriesError(f"exceeded max retries: {self.max_retries}")
        self._log_error(e)
        raise e

    def _run(self, inputs: dict, error_msg: str, **kwargs):
        """Run the chain.

        Args:
            inputs (dict): The inputs for the chain.
            error_msg (Exception): The error of the previous run.
            **kwargs: Keyword arguments for the chain.

        Returns:
            Any: The output of the chain.
        """

        # prepare
        inputs = self.prep_inputs(inputs, **kwargs)
        prompt = self.prep_prompt(error_msg, **inputs)
        inputs_ = self.format_inputs(prompt, inputs, **kwargs)
        self._debug(
            "Prompt",
            formatted_prompt=prompt.format(**inputs_)
        )

        # generate
        executor = self.prep_executor(prompt, **kwargs)
        text, run_metrics = self._call_executor(executor, inputs_)
        self._log_metrics(run_metrics)

        self.last_output = text
        self._debug(
            "Execution",
            generation_output=text,
            run_metrics=run_metrics
        )
        # parse
        output = self.parse_output(text, inputs)

        # validate
        self.validate_output(output, inputs)

        return output

    def prep_prompt(self, error_msg: str = None, **kwargs) -> str:
        """Prepare the prompt for the chain.

        Args:
            error_msg (Exception): The error message.
            **kwargs: Keyword arguments for the prompt.

        Returns:
            str: The prompt.
        """
        is_chat_mode = self.driver.prompt_mode() == "chat"
        if error_msg is None:
            return self.prompt_builder.build(chat_mode=is_chat_mode, **kwargs)

        error_remark = (
            "---\n"
            f"During last generation, errors were encountered for following output:\n{self.last_output}\n\n"
            f"{error_msg}\n"
            "---\n"
        )

        return self.prompt_builder.build(error=error_remark, chat_mode=is_chat_mode, **kwargs)

        # if isinstance(error, ParsingError):
        #     return self.prompt_builder.fix_parsing(error=str(error), **kwargs)
        #
        # if isinstance(error, ValidationError):
        #     return self.prompt_builder.fix_validation(error=str(error), **kwargs)
        #
        # return self.prompt_builder.build(**kwargs)

    def prep_executor(self, prompt: str, chat_prompt: dict = None, **kwargs) -> BaseGenerationDriver:
        """Prepare the executor for the chain.

        Args:
            prompt (str): The prompt for the chain.
            **kwargs: Keyword arguments for the executor.

        Returns:
            Any: The executor.
        """
        return self.driver.load_driver(prompt=prompt, **kwargs)

    def prep_inputs(self, inputs: dict, **kwargs) -> dict:
        """Analyzes input variables in prompt and prepares inputs for executor."""
        if self.partial_variables:
            inputs.update(self.partial_variables)
        return inputs

    def format_inputs(self, prompt: str, inputs: dict, **kwargs) -> dict:
        """Analyzes input variables in prompt and prepares inputs for executor."""
        self._debug("Format Inputs (Pre)", prompt=prompt, inputs=inputs, keyargs=kwargs)

        prompt, placeholder_map = prepare_inputs_placeholders(prompt, inputs, **kwargs)
        input_dict = format_inputs(placeholder_map)

        if self.debug:
            self._debug(
                "Format Inputs",
                placeholder_map=placeholder_map,
                formatted_inputs=input_dict,
                input_schema=self.input_model.template_schema,
                input_model=self.input_model
            )

        input_dict["input"] = self.input_model.dump_to_prompt(inputs, **kwargs)
        return input_dict

    # === output parsing ===

    def parse_output(self, text: str, inputs: dict):
        """Parse the output of the chain."""
        output_parser = OutputParser(
            self.output_model,  # type: ignore
            fix_by_llm=self.fix_parsing_by_llm,
            fix_partial_by_llm=self.fix_parsing_partially_by_llm,
            debug=self.debug
        )
        output, run_metrics, error_log = output_parser.parse(text, inputs)

        self._debug(
            "Output Parsing",
            parsed_output=output,
            error_log=error_log,
        )

        if self.return_metrics and run_metrics:
            for run_metrics in run_metrics:
                self._log_metrics(run_metrics)
        if error_log:
            for error in error_log:
                self._log_error(error)
        return output

    # === output validation ===

    def validate_output(self, output: dict, inputs: dict):
        """Validate the output of the chain.

        Args:
            output (Any): The output of the chain.
            inputs (dict): The inputs for the chain for extra variables used in output_schema.

        Returns:
            Any: The output of the chain.
        """

        validation_errors = self.validator.validate(output, inputs)
        if validation_errors:
            for error in validation_errors:
                self._log_error(error)
            raise ValidationError("Validation failed with errors")

    # === helpers ===

    @staticmethod
    def _prep_inputs(inputs: dict, input_keys: list) -> str:
        """Prepares inputs for executor."""
        return dump_to_yaml_string({k: inputs[k] for k in input_keys if k in inputs})

    @property
    def execution_type(self):
        return "sync"

    # def _remove_cot(self, output: dict):
    #     cot = []
    #     for key in ["reason", "chain-of-thoughts", "reasoning"]:
    #         if key in output:
    #             value = output.pop(key)
    #             if isinstance(value, list):
    #                 value = "\n".join(value)
    #             cot.append(value)
    #     if cot:
    #         self.cot = cot[0]
    #     return output
