from typing import Union

from structgenie.base import BaseEngine
from structgenie.engine.single import StructGenie

TEMPLATE_SEPERATOR = "%%%"


class StructChain(BaseEngine):
    """Prediction Chain."""
    templates: list[str]
    template_seperator: str = TEMPLATE_SEPERATOR
    default_engine: BaseEngine = StructGenie

    @classmethod
    def from_instruction(cls, instruction: str, **kwargs) -> "PredictionChain":
        """Build Prediction Chain from instruction."""
        return NotImplemented

    @classmethod
    def load_engine(cls, **kwargs) -> "PredictionChain":
        """Load Prediction Chain."""
        return NotImplemented

    @classmethod
    def from_template(
            cls,
            templates: Union[list[str], str],
            **kwargs) -> "PredictionChain":
        """Build Prediction Chain from template.

        Split templates by template_seperator and run engine in sequence.
        """

        if isinstance(templates, str):
            templates = [t.strip() for t in templates.split(TEMPLATE_SEPERATOR)]

        return cls(templates=templates, **kwargs)

    def run(self, inputs: dict, **kwargs):
        """Run Prediction Chain."""
        for i, template in enumerate(self.templates):
            engine = self.default_engine.from_template(template, **kwargs)
            outputs = engine.run(inputs, **kwargs)
            print(f"Finished run {i} of {len(self.templates) - 1} with: \n")
            print(outputs)
            print("\n=== Next run ===\n")
            inputs.update(outputs)

        return inputs
