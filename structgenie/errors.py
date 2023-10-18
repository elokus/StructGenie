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
    def __init__(self, msg: str, output: dict):
        self.msg = msg
        self.output = output

    def __str__(self):
        return f"{self.msg}\n\nParsed Output:\n{self.output}"


class ValidationRuleError(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"


class ValidationTypeError(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"


class ValidationKeyError(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"


class MultilineParsingError(Exception):
    pass


class YamlParsingError(Exception):
    pass
