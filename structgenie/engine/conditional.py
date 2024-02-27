from typing import Union

from structgenie.base import BaseIOModel, BaseValidator
from structgenie.components.examples import ExampleSelector
from structgenie.components.input_output import InputModel, OutputModel, init_output_model
from structgenie.components.prompt.builder import PromptBuilder
from structgenie.components.prompt.conditional_builder import ConditionalPromptBuilder
from structgenie.components.validation._object import validate_missing_keys, validate_unexpected_keys, required_keys
from structgenie.engine import StructEngine
from structgenie.errors import ValidationError
from structgenie.utils.templates import load_system_config


class ConditionalEngine(StructEngine):
    """Conditional Engine."""
    output_model_else: BaseIOModel = None
    validator_else: BaseValidator = None
    condition: str = None

    @classmethod
    def load_engine(
            cls,
            instruction: str,
            input_model: InputModel,
            output_model: OutputModel,
            examples: ExampleSelector = None,
            prompt_kwargs: dict = None,
            system_config: Union[dict, str] = None,
            output_model_else: BaseIOModel = None,
            condition: str = None,
            **kwargs) -> "StructGenie":

        from structgenie.components.validation import Validator

        if kwargs.get("partial_output_model"):
            output_model_ = init_output_model(output_model, partial_output_model=kwargs.get("partial_output_model"))
        else:
            output_model_ = output_model

        if kwargs.get("partial_output_model_else"):
            output_model_else_ = init_output_model(
                output_model_else, partial_output_model=kwargs.get("partial_output_model_else")
            )
        else:
            output_model_else_ = output_model_else

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
        prompt_builder = ConditionalPromptBuilder(
            instruction=instruction,
            examples=examples,
            output_model=output_model_,
            input_model=input_model,
            output_model_else=output_model_else_,
            condition=condition,
            **prompt_kwargs
        )
        validator = Validator.from_output_model(output_model_)
        validator_else = Validator.from_output_model(output_model_else_)

        return cls(
            instruction=instruction,
            prompt_builder=prompt_builder,
            validator=validator,
            output_model=output_model_,
            input_model=input_model,
            examples=examples,
            validator_else=validator_else,
            **kwargs
        )

    def check_condition(self, inputs: dict, output: dict) -> bool:
        """Check the condition.

        Check if the returned output meets the output_model or output_model_else

        Args:
            output (dict): The output of the chain.

        Returns:
            bool: The condition.
        """

        val_config_if = self.validator._parse_inputs(inputs)
        val_config_else = self.validator_else._parse_inputs(inputs)

        required_keys_if = len(required_keys(val_config_if))
        required_keys_else = len(required_keys(val_config_else))

        missing_keys_if = len(validate_missing_keys(output, val_config_if))
        missing_keys_else = len(validate_missing_keys(output, val_config_else))

        unexpected_keys_if = len(validate_unexpected_keys(output, val_config_if))
        unexpected_keys_else = len(validate_unexpected_keys(output, val_config_else))

        required_keys_if = 1 if required_keys_if == 0 else required_keys_if
        required_keys_else = 1 if required_keys_else == 0 else required_keys_else

        missing_if_ratio = missing_keys_if / required_keys_if
        missing_else_ratio = missing_keys_else / required_keys_else

        unexpected_if_ratio = unexpected_keys_if / required_keys_if
        unexpected_else_ratio = unexpected_keys_else / required_keys_else

        if missing_if_ratio < missing_else_ratio and unexpected_if_ratio < unexpected_else_ratio:
            return True

        elif missing_if_ratio > missing_else_ratio and unexpected_if_ratio > unexpected_else_ratio:
            return False

        elif missing_if_ratio < missing_else_ratio and unexpected_if_ratio > unexpected_else_ratio:
            return True

        return False

    def validate_output(self, output: dict, inputs: dict):
        """Validate the output of the chain.

        Selects the validator based on the condition and validates the output.

        Args:
            output (Any): The output of the chain.
            inputs (dict): The inputs for the chain for extra variables used in output_schema.

        Returns:
            Any: The output of the chain.
        """

        if self.check_condition(inputs, output):
            validator = self.validator
        else:
            validator = self.validator_else

        validation_errors = validator.validate(output, inputs)
        if validation_errors:
            errors = {f"Error_{i}": str(error) for i, error in enumerate(validation_errors)}
            self._log_message(
                "Validation Error",
                **errors,
            )
            for error in validation_errors:
                self._log_error(error)
            raise ValidationError("Validation failed with errors")
