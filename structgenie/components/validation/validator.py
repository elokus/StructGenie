from structgenie.base import BaseValidator
from structgenie.components.validation._content import validate_content
from structgenie.components.validation._object import *
from structgenie.components.validation._rule import validate_rules
from structgenie.components.validation._type import validate_type
from structgenie.errors import ValidationKeyError, ValidationTypeError, ValidationRuleError, ValidationContentError, \
    ValidatorExecutionError
from structgenie.utils.parsing import replace_placeholder_from_inputs_and_kwargs
from structgenie.utils.parsing.placeholder import has_placeholder


class Validator(BaseValidator):
    """Validate an output based on a key and a set of rules.

    Takes the valid values from one input key and validates the output based on those values.
    """
    validation_config: dict

    def __init__(self, validation_config: dict, output_model: BaseIOModel = None):
        self.validation_config = validation_config
        self.output_model = output_model
        self.error_log = []
        self.inputs = {}

    @classmethod
    def from_output_model(cls, output_model: BaseIOModel):
        """Build validator from output model"""
        return cls(validation_config=output_model.as_dict, output_model=output_model)

    def validate(self, output: dict, inputs: dict = None) -> Union[list, None]:
        """Validate the output based on the validation config."""
        if inputs:
            self.inputs = inputs

        validation_config = self._parse_inputs(self.inputs)

        try:
            self._validate(output, validation_config)
        except Exception as e:
            self.log_error_msg(f"Validator raised error: {e}")
            raise e

        error_log = [error for error in self.error_log if error]
        self.error_log = []
        self.inputs = {}
        return error_log

    def _validate(self, data: dict, validation_config: dict, parent_key: str = None):
        """Validate the output based on the validation config."""
        error_msg = validate_keys(data, validation_config)
        if error_msg:
            self.log_error_msg(error_msg, "key", parent_key)
            return

        if not isinstance(data, dict):
            return

        for key, value in data.items():
            self._validate_item(key, value, validation_config, parent_key=parent_key)

    def _validate_item(self, key: str, value: any, val_config: dict, parent_key: str = None):
        """Validate a single item in the output."""

        # validate type
        error_msg = validate_type(key, value, val_config)
        self.log_error_msg(error_msg, "type", parent_key)

        # validate rules
        error_msg = validate_rules(key, value, val_config)
        self.log_error_msg(error_msg, "rule", parent_key)

        # validate content
        error_msg = validate_content(key, value, val_config)
        self.log_error_msg(error_msg, "content", parent_key)

        # validate nested value
        self._validate_nested(key, value, val_config, parent_key)

    def _validate_nested(self, key: str, value: any, val_config: dict, parent_key: str = None):
        """Validate nested structure.

        Creates a new validation config for the nested structure.
        validates the nested structure with same logic by calling _validate().
        Parent key passed to log error messages with the correct key.
        """
        if not is_nested(key, val_config):
            return None

        new_parent_key = key if not parent_key else f"{parent_key}.{key}"

        if isinstance(value, dict):
            self.log_error_msg(
                nested_key_validation(key, value, self.output_model, inputs=self.inputs), "key",
                parent_key=new_parent_key
            )
            return self._validate(value, validation_config_nested(key, val_config), parent_key=new_parent_key)

        elif isinstance(value, list):
            self.log_error_msg(
                nested_key_validation(key, value, self.output_model, inputs=self.inputs), "key",
                parent_key=new_parent_key
            )
            for obj in value:
                self._validate(obj, validation_config_nested(key, val_config), parent_key=new_parent_key)

    def _parse_inputs(self, inputs: dict):
        """Parse the inputs to the correct format for validation."""
        val_config = {}
        for key, config in self.validation_config.items():
            val_config[key] = config.copy()
            if config["rule"] and has_placeholder(config["rule"]):
                val_config[key]["rule"] = replace_placeholder_from_inputs_and_kwargs(config["rule"], inputs)
        return val_config

    def log_error_msg(self, msg: Union[str, list[str]], error_type: str = None, parent_key: str = None):
        if not msg:
            return

        if isinstance(msg, list):
            for m in msg:
                self.log_error_msg(m, error_type, parent_key)
            return

        if error_type == "key":
            self.error_log.append(ValidationKeyError(msg, parent_key))
        elif error_type == "type":
            self.error_log.append(ValidationTypeError(msg, parent_key))
        elif error_type == "rule":
            self.error_log.append(ValidationRuleError(msg, parent_key))
        elif error_type == "content":
            self.error_log.append(ValidationContentError(msg, parent_key))
        else:
            self.error_log.append(ValidatorExecutionError(msg))
