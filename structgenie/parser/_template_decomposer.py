import re

INSTRUCTION_PATTERNS = [r"=== Instruction ===\n(.*)=== Instruction end ===", r"((.*?)(?=\n===|{input}|---))"]
EXAMPLE_PATTERN = [r"=== Examples ===\n(.*)=== Examples end ==="]
RESPONSE_SCHEMA_PATTERN = [r"=== Response Schema ===\n(.*)=== Response Schema end ===", r"(?<=---\n)(<.*>)"]
INPUT_SCHEMA_PATTERN = [r"=== Input Schema ===\n(.*)=== Input Schema end ===", r"(?<=---\n)(<.*>)"]
SYSTEM_INSTRUCTION = [r"{{!system: (.*)}}"]


def decompose_template(schema_template: str):
    """Decompose template into sections"""
    instruction = _extract_from_patterns(schema_template, INSTRUCTION_PATTERNS)
    examples = _extract_from_patterns(schema_template, EXAMPLE_PATTERN)
    output_schema = _extract_from_patterns(schema_template, RESPONSE_SCHEMA_PATTERN)
    return instruction, examples, output_schema


def extract_instruction_content(schema_template: str):
    """Extract instruction from template"""
    return _extract_from_patterns(schema_template, INSTRUCTION_PATTERNS)


def extract_examples_content(schema_template: str):
    """Extract examples from template"""
    return _extract_from_patterns(schema_template, EXAMPLE_PATTERN)


def extract_output_schema_content(schema_template: str):
    """Extract output schema from template"""
    return _extract_from_patterns(schema_template, RESPONSE_SCHEMA_PATTERN)


def extract_system_instruction(schema_template: str):
    """Extract system instruction from template"""
    return _extract_from_patterns(schema_template, SYSTEM_INSTRUCTION)


def _extract_from_patterns(template: str, patterns: list[str]):
    for pattern in patterns:
        match = re.search(pattern, template, re.DOTALL)
        if match:
            return match.group(1)
    return None


def _extract_from_pattern(template: str, pattern: str):
    match = re.search(pattern, template, re.DOTALL)
    if match:
        return match.group(1)
    return None
