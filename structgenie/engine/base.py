import uuid
from abc import abstractmethod
from typing import Union, Callable, Type

from pydantic import Field

from structgenie.base import BaseEngine, BaseGenerationDriver
from structgenie.prompt.builder import PromptBuilder
from structgenie.templates.load_config import load_system_config

from structgenie.input_output import load_input_schema, init_input_schema, OutputModel, load_output_model, \
    init_output_model
from structgenie.templates import extract_sections, load_default_template
from structgenie.examples import ExampleSelector
from structgenie.driver import LangchainDriverBasic
from structgenie.parser import parse_yaml_string
from structgenie.validation.validator import Validator


class SinglePredictionEngine(BaseEngine):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4().hex))

    # executor
    driver: Type[BaseGenerationDriver] = LangchainDriverBasic

    # prompt
    prompt_builder: PromptBuilder = None

    # validation settings
    validator: Validator = None

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
        sections = extract_sections(schema_template)

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
            **kwargs) -> "BasePredictionEngine":
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
            **kwargs) -> "BasePredictionEngine":

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

    @abstractmethod
    def run(self, **kwargs):
        pass
