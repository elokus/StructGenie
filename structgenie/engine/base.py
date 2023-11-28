import uuid
from abc import abstractmethod, ABC
from typing import Union, Type, Tuple

from pydantic import BaseModel, Field

from structgenie.base import BasePromptBuilder, BaseValidator, BaseGenerationDriver, BaseIOModel
from structgenie.components.examples import ExampleSelector
from structgenie.components.input_output import (
    OutputModel,
    load_output_model,
    init_output_model,
    InputModel,
    load_input_model,
    init_input_model
)
from structgenie.driver.openai import OpenAIDriver
from structgenie.errors import EngineRunError, ParsingError, ValidationError
from structgenie.utils.templates import (
    extract_sections, load_default_template, load_system_config
)

DEFAULT_RUN_METRICS = {
    "execution_time": 0,
    "token_usage": 0,
    "model_name": None,
    "model_config": None,
    "failure_rate": 0,
    "errors": [],
}


class BaseEngine(BaseModel, ABC):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4().hex))
    run_metrics: dict = DEFAULT_RUN_METRICS

    # executor
    driver: Type[BaseGenerationDriver] = OpenAIDriver

    # prompt
    prompt_builder: BasePromptBuilder = None

    # validation settings
    validator: BaseValidator = None

    # parser
    fix_parsing_by_llm: bool = True
    fix_parsing_partially_by_llm: bool = True

    # run settings
    max_retries: int = 4
    input_schema: str = None
    input_model: BaseIOModel = None
    output_model: BaseIOModel = None
    examples: ExampleSelector = None
    instruction: str = None
    debug: bool = False
    raise_errors: bool = False
    return_metrics: bool = True

    # run states
    last_error: Union[str, None] = None
    last_output: Union[str, None] = None
    partial_variables: dict = None

    return_reasoning: bool = False
    num_metrics_logged: int = 0

    class Config:
        arbitrary_types_allowed = True

    # === Setters ===

    def set_example_selector(self, examples: ExampleSelector):
        self.prompt_builder.examples = examples
        self.examples = examples

    def set_instruction(self, instruction: str):
        self.prompt_builder.instruction = instruction
        self.instruction = instruction

    def set_output_model(self, output_model: OutputModel):
        from structgenie.components.validation import Validator
        self.prompt_builder.output_model = output_model
        self.validator = Validator.from_output_model(output_model)
        self.output_model = output_model

    # === RUN ===

    @abstractmethod
    def run(self, input_data: dict, **kwargs) -> dict:
        pass

    async def apply(self, *args, **kwargs):
        return NotImplemented

    # === INITIALIZATION ===

    @classmethod
    def from_defaults(cls, template_name: str, **kwargs):
        template = load_default_template(template_name)
        return cls.from_template(template, **kwargs)

    @classmethod
    def from_template(
            cls,
            schema_template: str,
            output_model: Union[OutputModel, dict, str] = None,
            prompt_kwargs: dict = None,
            partial_output_model: dict[str, Union[OutputModel, dict, str]] = None,
            **kwargs):
        """Build Prediction Engine from template."""
        sections = extract_sections(schema_template.strip())

        system_config = sections.get("system_config")
        instruction = sections.get("instruction")
        examples = ExampleSelector.load_examples(sections.get("examples"))
        output_model_ = load_output_model(
            sections, examples, output_model=output_model, partial_output_model=partial_output_model
        )
        input_model_ = load_input_model(sections, examples, input_model=kwargs.get("input_model"))

        return cls.load_engine(
            instruction=instruction,
            input_model=input_model_,
            output_model=output_model_,
            examples=examples,
            prompt_kwargs=prompt_kwargs,
            system_config=system_config,
            **kwargs
        )

    @classmethod
    def from_instruction(
            cls,
            instruction: str,
            input_schema: Union[str, dict, list] = None,
            output_model: Union[OutputModel, dict, str] = None,
            examples: Union[str, list] = None,
            prompt_kwargs: dict = None,
            partial_output_model: dict[str, Union[OutputModel, dict, str]] = None,
            **kwargs) -> "StructGenie":
        """Build Prediction Engine from instructions."""
        if examples:
            examples = ExampleSelector.load_examples(examples)

        output_model_ = init_output_model(output_model, examples=examples, partial_output_model=partial_output_model)
        input_model_ = init_input_model(input_schema, examples=examples)

        return cls.load_engine(
            instruction=instruction,
            input_model=input_model_,
            output_model=output_model_,
            examples=examples,
            prompt_kwargs=prompt_kwargs,
            **kwargs
        )

    @classmethod
    def load_examples(cls, examples: Union[str, list] = None):
        """Load examples from a string, list or file."""
        return ExampleSelector.load_examples(examples)

    @classmethod
    def load_engine(
            cls,
            instruction: str,
            input_model: InputModel,
            output_model: OutputModel,
            examples: ExampleSelector = None,
            prompt_kwargs: dict = None,
            system_config: Union[dict, str] = None,
            **kwargs) -> "StructGenie":

        from structgenie.components.prompt.builder import PromptBuilder
        from structgenie.components.validation import Validator

        if kwargs.get("partial_output_model"):
            output_model_ = init_output_model(output_model, partial_output_model=kwargs.get("partial_output_model"))
        else:
            output_model_ = output_model

        kwargs = kwargs or {}

        system_config = load_system_config(system_config)
        if system_config["engine"]:
            _kwargs = system_config
            _kwargs.update(kwargs)
            kwargs = _kwargs

        if system_config["partial_variables"]:
            if kwargs.get("partial_variables"):
                partial_variables = system_config["partial_variables"]
                partial_variables.update(kwargs["partial_variables"])
                kwargs["partial_variables"] = partial_variables
            else:
                kwargs["partial_variables"] = system_config["partial_variables"]

        prompt_kwargs = prompt_kwargs or {}
        prompt_builder = PromptBuilder(
            instruction=instruction,
            examples=examples,
            output_model=output_model,
            input_model=input_model,
            **prompt_kwargs
        )
        validator = Validator.from_output_model(output_model)

        return cls(
            instruction=instruction,
            prompt_builder=prompt_builder,
            validator=validator,
            output_model=output_model_,
            input_model=input_model,
            examples=examples,
            **kwargs
        )

    # === Log/Debug ===

    def _log_metrics(self, metrics: dict):
        """Log run metrics.

        Remarks: Model name and config are only logged if not already set because output_fixing run
        could have different model and config.
        """

        if not metrics:
            metrics = {}

        inc_fr = 0 if self.num_metrics_logged == 0 else 1

        if not self.run_metrics["model_name"]:
            self.run_metrics["model_name"] = metrics.get("model_name", None)

        if not self.run_metrics["model_config"]:
            self.run_metrics["model_config"] = metrics.get("model_config", None)

        self.run_metrics["token_usage"] += metrics.get("token_usage", 0)
        self.run_metrics["execution_time"] += metrics.get("execution_time", 0)
        self.run_metrics["failure_rate"] += metrics.get("failure_rate", inc_fr)
        self.run_metrics["errors"].extend(metrics.get("errors", []))
        self.num_metrics_logged += 1

    def _log_error(self, error: Exception):
        """Log error in run_metrics."""
        self.run_metrics["errors"].append(error)

    # TODO: Add debug logging to file
    def _debug(self, step_context: str, **kwargs):
        """Print debug information."""
        if self.debug:
            print(f"=== {step_context} ===")
            for key, value in kwargs.items():
                key_ = key.replace("_", " ").capitalize()
                print(f"{key_}: {value}")

    # === Execute Generation ===

    def _call_executor(
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
            result, run_metrics = executor.predict_and_measure(**inputs)
            self._log_metrics(run_metrics)
        else:
            result, run_metrics = executor.predict(**inputs), None

        return result, run_metrics

    # === Error Handling ===

    def _on_run_error(self, e, error_index, n_run, raise_error):
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
            new_errors=self.last_error,
            error_index=error_index,
            run_metrics=self.run_metrics["errors"]
        )
        n_run += 1
        return n_run, error_index
