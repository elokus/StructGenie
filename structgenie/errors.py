class ParsingError(Exception):
    def __init__(self, msg: str, text: str):
        self.msg = msg
        self.generated_text = text

    def __str__(self):
        return f"{self.msg}\n\nGenerated Text:\n{self.generated_text}"


class ValidationError(Exception):
    def __init__(self, msg: str, output: dict):
        self.msg = msg
        self.output = output

    def __str__(self):
        return f"{self.msg}\n\nParsed Output:\n{self.output}"


class TemplateError(Exception):
    pass
