import asyncio
from typing import Union, Tuple

from structgenie.base import BaseGenerationDriver
from structgenie.engine.genie import StructEngine


class AsyncEngine(StructEngine):

    async def apply(self, input_list: list[dict], **kwargs):
        return await asyncio.gather(*[self.run(input_data, **kwargs) for input_data in input_list])

    async def run(self, inputs: dict, **kwargs) -> Union[dict, Tuple[dict, dict]]:
        """Run the chain.

        Args:
            inputs (dict): The inputs for the chain.
            **kwargs: Keyword arguments for the chain.

        Returns:
            Any: The output of the chain.
        """
        self.last_error = None

        n_run = 0
        while n_run <= self.max_retries:
            try:
                output = await self._run(inputs, self.last_error, **kwargs)
                if self.return_metrics:
                    return output, self.run_metrics
                return output
            except Exception as e:
                self.last_error = e
                n_run += 1
                if self.debug:
                    print(f"Error: {e}")
                    raise e
                if self.return_metrics:
                    self._log_error(e)

    async def _run(self, inputs: dict, error: Exception, **kwargs) -> dict:
        """Run the chain.

        Args:
            inputs (dict): The inputs for the chain.
            error (Exception): The error of the previous run.
            **kwargs: Keyword arguments for the chain.

        Returns:
            Any: The output of the chain.
        """

        # prepare
        inputs = self.prep_inputs(inputs, **kwargs)
        prompt = self.prep_prompt(error, **inputs)
        inputs_ = self.format_inputs(prompt, inputs, **kwargs)
        executor = self.prep_executor(prompt, **kwargs)

        if self.debug:
            print(prompt.format(**inputs_))

        # generate
        if self.return_metrics:
            text, run_metrics = await self._call_executor(executor, inputs_, return_metrics=True)
            self._log_metrics(run_metrics)
        else:
            text = await self._call_executor(executor, inputs_)
        # parse
        output = self.parse_output(text, inputs)
        # validate
        self.validate_output(output, inputs)

        return output

    @staticmethod
    async def _call_executor(
            executor: BaseGenerationDriver,
            inputs: dict,
            return_metrics: bool = False
    ) -> Union[str, Tuple[str, dict]]:
        """Call the executor.

        Args:
            executor (Any): The executor.
            inputs (dict): The inputs for the executor.
            return_metrics (bool, optional): Whether to return the metrics. Defaults to False.

        Returns:
            str: The output of the executor.
        """
        if return_metrics:
            return await executor.predict_and_measure_async(**inputs)
        return await executor.predict_async(**inputs)

    @property
    def execution_type(self):
        return "async"
