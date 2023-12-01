import asyncio
from typing import Union, Tuple

from structgenie.base import BaseGenerationDriver
from structgenie.engine.genie import StructEngine
from structgenie.errors import EngineRunError, ParsingError, ValidationError, MaxRetriesError


class AsyncEngine(StructEngine):

    async def apply(self, input_list: list[dict], **kwargs):
        return await asyncio.gather(*[self.run(input_data, **kwargs) for input_data in input_list])

    async def run(self, inputs: dict, raise_error: bool = False, **kwargs) -> Union[dict, Tuple[dict, dict]]:
        """Run the chain.

        Args:
            inputs (dict): The inputs for the chain.
            raise_error (bool): If True, errors will be raised.
            **kwargs: Keyword arguments for the chain.

        Returns:
            Any: The output of the chain.
        """
        self.last_error = None
        error_index = 0

        n_run = 0
        while n_run <= self.max_retries:
            try:
                output = await self._run(inputs, error_msg=self.last_error, **kwargs)
                if self.return_metrics:
                    self.errors_to_string()
                    return output, self.run_metrics
                return output

            except Exception as e:
                n_run, error_index = self._on_run_error(e, error_index, n_run, raise_error)

        e = MaxRetriesError(f"exceeded max retries: {self.max_retries}")
        self._log_error(e)
        raise e

    async def _run(self, inputs: dict, error_msg: str, **kwargs):
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
        self._log_message(
            "Prompt",
            formatted_prompt=prompt.format(**inputs_)
        )

        # generate
        executor = self.prep_executor(prompt, **kwargs)
        text, run_metrics = await self._call_executor(executor, inputs_)
        self._log_metrics(run_metrics)

        self.last_output = text
        self._log_message(
            "Execution",
            generation_output=text,
            run_metrics=run_metrics
        )
        # parse
        output = self.parse_output(text, inputs)

        # validate
        self.validate_output(output, inputs)

        return output

    async def _call_executor(
            self,
            executor: BaseGenerationDriver,
            inputs: dict,
    ) -> Union[Tuple[str, None], Tuple[str, dict]]:
        """Call the executor.

        Args:
            executor (Any): The executor.
            inputs (dict): The inputs for the executor.
        Returns:
            str: The output of the executor.
            dict|None: run_metric if return_metrics is True
        """
        if self.return_metrics:
            result, run_metrics = await executor.predict_and_measure_async(**inputs)
            self._log_metrics(run_metrics)
        else:
            result = await executor.predict_async(**inputs)
            run_metrics = None

        return result, run_metrics

    @property
    def execution_type(self):
        return "async"
