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


# === VALIDATION ERRORS ===

class ValidationError(Exception):
    def __init__(self, msg: str, parent_key: str = None):
        self.msg = msg
        self.parent_key = parent_key

    def __str__(self):
        if self.parent_key:
            return f"{self.__class__.__name__}: {self.msg}\nFor nested output key '{self.parent_key}'\n"
        return f"Error: {self.msg}\n"


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
    def __init__(self, msg: str, text: str):
        self.msg = msg
        self.generated_text = text

    def __str__(self):
        return f"{self.msg}\n\nGenerated Text:\n{self.generated_text}"


class ParsingPartialError(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"


class ParsingFixingError(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"


class MultilineParsingError(Exception):
    pass


class YamlParsingError(Exception):
    pass
