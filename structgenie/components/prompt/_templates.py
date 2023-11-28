DEFAULT_TEMPLATE = """{instruction}
{format_instructions}
{examples}
{remarks}
{input}
"""
CHAT_TEMPLATE = """<%system%>
{instruction}
{format_instructions}
</%system%>
<%examples%>
{examples}
</%examples%>
<%user%>
{remarks}
{input}
</%user%>
"""

CHAT_TEMPLATE_ON_ERROR = """<%system%>
{instruction}
{format_instructions}
</%system%>
<%examples%>
{examples}
</%examples%>
<%user%>
{remarks}
{input}
</%user%>
<%last_output%>
{last_output}
</%last_output%>
<%user_error%>
Your response is not valid and caused the following error:
{error}
</%user_error%>
"""

DEFAULT_SCHEMA_TEMPLATE = """{instruction}
{examples}
{remarks}
{input}
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
During last attempt, the following errors were encountered:
{error}
This error was due to your response:
{last_output}
Please fix the error and try again."""



FIX_PARSING_ERROR_TEMPLATE = """The output from a previous generation task runs into a parsing error. The error is raised during parsing a string output with yaml.load() function.
This is often caused by a non-ascii character in the output, wrong multiline string format or characters like ":" in the output string that interfere with the yaml format.
Please try to fix the output provided below so that it can be parsed by yaml.load() function according to following format instructions:
{format_instructions}
{remarks}
{input}"""
