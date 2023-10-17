# StructGenie Documentation

## Overview

**StructGenie** is a sophisticated yet easy-to-use engine designed for the generation and validation of structured
outputs from large language models (LLMs). The uniqueness of StructGenie lies in its ability to streamline the
configuration process through a single, intuitive input template. This template, supporting a myriad of syntaxes, acts
as the central hub for defining the generation task, its constraints, and the expected structured outputs.

### Key Features:

1. **Unified Template Configuration**: Simplify your generation tasks using a single input template. This holistic
   approach eliminates the need to juggle multiple configuration files or settings.
2. **Multifaceted Syntax Support**: Catering to a wide range of use-cases, StructGenie supports multiple syntaxes within
   its template, ensuring flexibility and ease of use.
3. **Dynamic Output Parsing**: Leveraging the power of the LLMs, StructGenie parses generated outputs into a structured
   dictionary format, enabling straightforward data extraction and further processing.
4. **Integrated Validation**: With embedded validation rules within the template, StructGenie ensures the outputs
   conform to the desired structure and type, guaranteeing both accuracy and consistency.
5. **Framework-agnostic Execution**: Thanks to a versatile executor driver, StructGenie seamlessly integrates with
   various LLM API frameworks.
6. **Example Selector**: Pass a path to an example file or list your examples directly in the prompt. The
   ExampleSelector will take care of selecting the best examples according to the token limitations.
6. **YAML Syntax**: Using YAML as the default syntax for examples, input and outputs instructions, StructGenie provides
   a clean and intuitive template structure, making it easy to learn and use, while minimizing the token usage.
7. **System Instructions**: Call system instructions/functions directly from the template, allowing for a more
   streamlined generation process e.g.: `{{!system:load_file("examples.yaml")}}`

## Installation Guide

To embark on your journey with StructGenie:
> **Note**: Python 3.9 or higher is recommended for a smooth experience with StructGenie. Make sure to have langchain
> installed as well.

### Option 1: Installation from GitHub

```bash
# Clone the repository (assuming it's hosted on GitHub)
git clone https://github.com/elokus/StructGenie.git

# Transition into the project directory
cd StructGenie

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Installation from PyPI

```bash
# Install the project (ensure you have a Python environment set up)
pip install structgenie
```

## Usage Examples

### Generation from a simple Template

```python
from structgenie.engine import StructGenie

# Define your input template
template = """
Generate a Person for each of the following family roles:
{family_roles}

Begin!
Family Members: {family_roles}
---
Family: <list (for each $role in {family_roles})>
Family.$role: <dict>
Family.$role.name: <str>
Family.$role.age: <int>
"""

# Initialize StructGenie with the template
genie = StructGenie.from_template(template)

# Supply your inputs in dictionary format
inputs = {
    "family_roles": ["Father", "Mother", "Son", "Daughter"]
}

# Run the generation task
result = genie.run(inputs)

# Enjoy your structured result!
print(result)
```

Which returns:

```json
{
  'family': [
    {
      'father': {
        'name': 'John',
        'age': 40
      }
    },
    {
      'mother': {
        'name': 'Emily',
        'age': 38
      }
    },
    {
      'son': {
        'name': 'Ethan',
        'age': 12
      }
    },
    {
      'daughter': {
        'name': 'Olivia',
        'age': 8
      }
    }
  ]
}
```

### Template Structure

The input configuration of StructGenie is done by templates. The template is divided into four sections:**Instruction**,
**Examples**, **Input** and **Output**. You can additionally pass also an **System Config** for setting template
internal variables and setting attributes for the underlying engine.
You can select different styles for your template to wrap each sections:

```perl
SEPERATOR_STYLE: === {section} ===, === {section} end ===
HTML_TAG_STYLE: <{section}>, </{section}>
GUIDANCE_STYLE: {{#{section}~}}, {{~/{section}}}
MARKDOWN_STYLE: # {section}, # ---
MARKDOWN_STYLE2: # {section}, # {section} end
```

You do not need to use the end tags for the sections. The engine will automatically detect the end of the section. The
default style is the MARKDOWN_STYLE.
As shown in the above example.
When no instruction tag is present the first paragraph is parsed as **Instruction section**.
The **Input Section** can also be introduced by simply adding 'Begin!' beforehand. The **Output Section** can be
introduced by adding '---' after the **Input Section** at the end of your template.
The recommanded template should have the following structure:

```perl
# Instruction
...
# Examples
...
# Input
...
# Output
...
```

## RoadMap

Our development plans for **StructGenie** include:

1. **Version 0.0.1**: Initial release with core functionalities.
2. **Validation Rules**: Adding a set of validation rules for more robust structured outputs.
3. **OptimizationEngine Release**: Launching the OptimizationEngine to enhance template effectiveness.

## OptimizationEngine (Moved to separate Project -> LLMP)

**OptimizationEngine** is an addition to StructGenie that aims to test and improve templates for LLM generation tasks.

### How it Works:

1. **Testing**: The engine uses random examples from the provided template. These examples contain both the input and
   the expected output.
2. **Evaluation**: The generation tasks are run to check if the LLM can produce the expected output.
3. **Optimization**: If the output is not as expected, OptimizationEngine adjusts the prompt's instruction and can
   create more examples. The goal is to improve the LLM's output accuracy.

The OptimizationEngine provides a methodical approach to refining templates for better results from language models.

## Contributing

We welcome contributions! Please see our contributing guide for more details.

## License

StructGenie is open source software licensed under the [MIT license](LICENSE).
