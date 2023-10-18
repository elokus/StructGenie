from structgenie.base import BaseValidator, BaseIOModel
from structgenie.components.validation._content import validate_content
from structgenie.components.validation._object import *
from structgenie.components.validation._rule import validate_rules
from structgenie.components.validation._type import validate_type
from structgenie.utils.parsing import replace_placeholder_from_inputs_and_kwargs, dump_to_yaml_string
from structgenie.utils.parsing.placeholder import has_placeholder


class Validator(BaseValidator):
    """Validate an output based on a key and a set of rules.

    Takes the valid values from one input key and validates the output based on those values.
    """
    validation_config: dict

    def __init__(self, validation_config: dict):
        self.validation_config = validation_config

    @classmethod
    def from_output_model(cls, output_model: BaseIOModel):
        """Build validator from output model"""
        return cls(validation_config=output_model.as_dict)

    def validate(self, output: dict, inputs: dict) -> Union[str, None]:
        """Validate the output based on the validation config."""

        validation_config = self._parse_inputs(inputs)
        try:
            validation_errors = self._validate(output, validation_config)
        except Exception as e:
            return f"Error {e} validating output: {dump_to_yaml_string(output)}"

        if validation_errors:
            return "\n".join(validation_errors) + f"\nFor output: {dump_to_yaml_string(output)}"
        return None

    def _validate(self, data: dict, validation_config: dict) -> list[str]:
        """Validate the output based on the validation config."""
        key_errors = validate_keys(data, validation_config)
        if key_errors:
            return [key_errors]

        return [error for error in self._validate_items(data, validation_config) if error]

    def _validate_items(self, d: dict, val_config: dict) -> Union[list[str], None]:
        errors = []
        for key, value in d.items():
            errors += self._validate_item(key, value, val_config)
        return errors

    def _validate_item(self, key, value, val_config) -> list[str]:

        errors = []
        # validate type
        errors += [validate_type(key, value, val_config)]

        # validate rules
        errors += [validate_rules(key, value, val_config)]

        # validate nested value
        errors += self._validate_nested(key, value, val_config)

        # validate content
        errors += [validate_content(key, value, val_config)]

        return errors

    def _validate_nested(self, key, value, val_config):
        errors = []

        if not is_nested(key, val_config):
            return errors

        if isinstance(value, dict):
            return self._validate(value, validation_config_nested(key, val_config))

        elif isinstance(value, list):
            for obj in value:
                errors += self._validate(obj, validation_config_nested(key, val_config))

        return errors

    def _parse_inputs(self, inputs: dict):
        """Parse the inputs to the correct format for validation."""
        val_config = {}
        for key, config in self.validation_config.items():
            val_config[key] = config.copy()
            if config["rule"] and has_placeholder(config["rule"]):
                val_config[key]["rule"] = replace_placeholder_from_inputs_and_kwargs(config["rule"], inputs)
        return val_config
