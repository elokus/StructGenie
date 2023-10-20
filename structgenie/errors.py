class PromptError(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"


class TemplateError(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"


class EngineRunError(Exception):
    def __init__(self, msg: str, context_error: Exception = None):
        self.msg = msg
        self.context = context_error.__class__.__name__ if context_error else None

    def __str__(self):
        if self.context:
            return f"{self.__class__.__name__}({self.msg} | Reason: {self.context})"
        return f"{self.__class__.__name__}({self.msg})"


class MaxRetriesError(EngineRunError):
    pass


# === VALIDATION ERRORS ===

class ValidationError(Exception):
    def __init__(self, msg: str, parent_key: str = None):
        self.msg = msg
        self.parent_key = parent_key

    def __str__(self):
        if self.parent_key:
            return f"{self.__class__.__name__}( {self.msg} > for key '{self.parent_key}')"
        return f"{self.__class__.__name__}( {self.msg} )"


class ValidatorExecutionError(ValidationError):
    pass


class ValidationRuleError(ValidationError):
    pass


class ValidationTypeError(ValidationError):
    pass


class ValidationKeyError(ValidationError):
    pass


class ValidationContentError(ValidationError):
    pass


# === PARSING ERRORS ===

class ParsingError(Exception):
    def __init__(self, msg: str, text: str = None):
        self.msg = msg
        self.generated_text = text

    def __str__(self):
        if self.generated_text:
            return f"{self.__class__.__name__}( {self.msg} > From parsing {self.generated_text} )"
        return f"{self.__class__.__name__})( {self.msg} )"


class ParsingPartialError(ParsingError):
    pass


class ParsingFixingError(ParsingError):
    pass


class MultilineParsingError(ParsingError):
    pass


class YamlParsingError(ParsingError):
    pass
