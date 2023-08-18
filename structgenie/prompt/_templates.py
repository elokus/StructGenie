DEFAULT_TEMPLATE = """{instruction}
{format_instructions}
{examples}
{remarks}
{input}
"""
DEFAULT_SCHEMA_TEMPLATE = """{instruction}
{examples}
{remarks}
{input}
---
{output_schema}
"""
FORMAT_INSTRUCTIONS_TEMPLATE = """Please return a response in yaml format using the following schema:
```yaml
{response_schema}
```
Do not include any other information or explanation to your response, 
so that your response can be parsed with yaml.safe_load().
Remember to set the value in quotes using the Double quotation marks 
when values are multiline strings or contain ':'."""
ERROR_TEMPLATE = """{remarks}
The following error occurred during your last attempt:
{error}
Please fix the error and try again."""
