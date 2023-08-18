import uuid
from typing import Union, Callable, Type
from pydantic import BaseModel, Field

from structgenie.errors import ParsingError, ValidationError
from structgenie.base import BasePromptBuilder, BaseValidator, BaseGenerationDriver
from structgenie.input_output import (
    load_input_schema,
    init_input_schema,
    OutputModel,
    load_output_model,
    init_output_model
)
from structgenie.operator.default import parse_default
from structgenie.templates import (
    extract_sections, load_default_template, load_system_config
)
from structgenie.parser import (
    parse_yaml_string,
    dump_to_yaml_string,
    format_inputs,
    prepare_inputs_placeholders
)
from structgenie.examples import ExampleSelector
from structgenie.driver import LangchainDriverBasic


class StructGenie(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4().hex))

    # executor
    driver: Type[BaseGenerationDriver] = LangchainDriverBasic

    # prompt
    prompt_builder: BasePromptBuilder = None

    # validation settings
    validator: BaseValidator = None

    # parser
    output_parser: Callable = parse_yaml_string
    output_fixing_parser: Callable = None

    # run settings
    max_retries: int = 4
    input_schema: str = None
    output_model: OutputModel = None
    examples: ExampleSelector = None
    instruction: str = None
    debug: bool = False

    # run states
    last_error: Union[Exception, None] = None
    partial_variables: dict = None

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_defaults(cls, template_name: str, **kwargs):
        template = load_default_template(template_name)
        return cls.from_template(template, **kwargs)

    @classmethod
    def from_template(
            cls,
            schema_template: str,
            output_model: Union[OutputModel, dict] = None,
            prompt_kwargs: dict = None,
            **kwargs):
        """Build Prediction Engine from template."""
        sections = extract_sections(schema_template.strip())

        system_config = sections.get("system_config")
        instruction = sections.get("instruction")
        examples = ExampleSelector.load_examples(sections.get("examples"))
        output_model = load_output_model(sections, examples, output_model=output_model)
        input_schema = load_input_schema(sections, examples)

        return cls.load_engine(
            instruction=instruction,
            input_schema=input_schema,
            output_model=output_model,
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
            output_model: Union[OutputModel, dict] = None,
            examples: Union[str, list] = None,
            prompt_kwargs: dict = None,
            **kwargs) -> "StructGenie":
        """Build Prediction Engine from instructions."""
        if examples:
            examples = ExampleSelector.load_examples(examples)

        output_model = init_output_model(output_model, examples=examples)
        input_schema = init_input_schema(input_schema, examples=examples)

        return cls.load_engine(
            instruction=instruction,
            input_schema=input_schema,
            output_model=output_model,
            examples=examples,
            prompt_kwargs=prompt_kwargs,
            **kwargs
        )

    @classmethod
    def load_engine(
            cls,
            instruction: str,
            input_schema: str,
            output_model: OutputModel,
            examples: ExampleSelector = None,
            prompt_kwargs: dict = None,
            system_config: Union[dict, str] = None,
            **kwargs) -> "StructGenie":
        from structgenie.prompt.builder import PromptBuilder
        from structgenie.validation.validator import Validator

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
            input_schema=input_schema,
            **prompt_kwargs
        )
        validator = Validator.from_output_model(output_model)

        return cls(
            instruction=instruction,
            prompt_builder=prompt_builder,
            validator=validator,
            output_model=output_model,
            input_schema=input_schema,
            examples=examples,
            **kwargs
        )

    def run(self, inputs: dict, **kwargs):
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
                return self._run(inputs, self.last_error, **kwargs)
            except Exception as e:
                print(f"Error: {e}")
                self.last_error = e
                n_run += 1
                raise e

    def _run(self, inputs: dict, error: Exception, **kwargs):
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
            print("Prompt:")
            print(prompt)
            print("Inputs:")
            print(inputs_)
            print("Formatted Prompt:")
            print(prompt.format(**inputs_))

        # generate
        text = self._call_executor(executor, inputs_)
        # parse
        output = self.parse_output(text, inputs)
        # validate
        self.validate_output(output, inputs)

        return output

    def prep_prompt(self, error: Exception = None, **kwargs) -> str:
        """Prepare the prompt for the chain.

        Args:
            error (Exception): The error message.
            **kwargs: Keyword arguments for the prompt.

        Returns:
            str: The prompt.
        """
        if error is None:
            return self.prompt_builder.build(**kwargs)

        if isinstance(error, ParsingError):
            return self.prompt_builder.fix_parsing(error=str(error), **kwargs)

        if isinstance(error, ValidationError):
            return self.prompt_builder.fix_validation(error=str(error), **kwargs)

    def prep_executor(self, prompt: str, **kwargs) -> BaseGenerationDriver:
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
            print(inputs)
        return inputs

    def format_inputs(self, prompt: str, inputs: dict, **kwargs) -> dict:
        """Analyzes input variables in prompt and prepares inputs for executor."""
        prompt, placeholder_map = prepare_inputs_placeholders(prompt, inputs, **kwargs)
        return format_inputs(placeholder_map, self.input_schema)

    # === output parsing ===

    def parse_output(self, text: str, inputs: dict) -> dict:
        """Parse the outputs of the chain.

        Args:
            text (str): The output of the chain.

        Returns:
            Dict: The parsed output.

        Raises:
            ParsingError: If the output could not be parsed.
        """
        try:
            output = self.output_parser(text)
        except Exception as e:
            output = self._parse_output(text, e)
        return self._parse_defaults(output, inputs)

    def _parse_output(self, text: str, error: Exception) -> dict:
        """Run output fixing parser if defined."""

        if not self.output_fixing_parser:
            raise ParsingError(f"Error while parsing output: {error}", text)

        try:
            return self.output_fixing_parser(text, output_keys=self.output_model.output_keys)

        except Exception as e:
            raise ParsingError(
                f"Could neither parse nor fix parsing error. Parsing error: {error}. Fixing error: {e}",
                text
            )

    def _parse_defaults(self, output: dict, inputs):
        return parse_default(output, self.output_model, **inputs)

    # === output validation ===

    def validate_output(self, output: dict, formatted_inputs: dict):
        """Validate the output of the chain.

        Args:
            output (Any): The output of the chain.

        Returns:
            Any: The output of the chain.
        """

        validation_errors = self.validator.validate(output, formatted_inputs)
        if validation_errors:
            raise ValidationError(f"Validation failed with errors:\n{validation_errors}", output)

    @staticmethod
    def _call_executor(executor: BaseGenerationDriver, inputs: dict) -> str:
        """Call the executor.

        Args:
            executor (Any): The executor.
            inputs (dict): The inputs for the executor.

        Returns:
            str: The output of the executor.
        """
        return executor.predict(**inputs)

    @staticmethod
    def _prep_inputs(inputs: dict, input_keys: list) -> str:
        """Prepares inputs for executor."""
        return dump_to_yaml_string({k: inputs[k] for k in input_keys if k in inputs})
