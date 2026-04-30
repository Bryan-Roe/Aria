# Code Generation Guide for Aria

This guide shows how to use the built-in code generation capabilities in the Aria project.

## Quick Start

The Aria project has **three main code generation systems**:

### 1. Safe Python Tool Generation (ToolMaker)

Generate validated Python functions with safety guardrails:

```bash
# In Copilot Chat, use:
@llm-maker Generate a function that validates email addresses

# Or use directly:
python3 -c "
from ai_projects.llm_maker.src.tool_maker import ToolMaker
maker = ToolMaker()
code = maker.create_tool(
    'validate_email',
    'Validates if a string is a valid email address',
    {'email': 'str'},
    {'is_valid': 'bool'}
)
print(code)
"
```

**Key Features:**

- ✅ AST-based safety validation (blocks dangerous imports)
- ✅ Automatic retry on validation failure
- ✅ Type hints and docstrings
- ✅ No external dependencies required
- ❌ Cannot use: `os`, `sys`, `subprocess`, `socket`, `urllib`, `eval`, `exec`

### 2. Complete Website Generation (WebsiteMaker)

Generate full HTML/CSS/JavaScript websites:

```bash
# In Copilot Chat, use:
@llm-maker Build a portfolio website with About and Contact pages

# Or use directly:
python3 -c "
from ai_projects.llm_maker.src.website_maker import WebsiteMaker
maker = WebsiteMaker()
result = maker.create_website(
    'my-portfolio',
    ['index.html', 'about.html', 'contact.html'],
    'A professional portfolio website'
)
print(result)
"
```

**Output Structure:**

```
my-portfolio/
├── index.html
├── style.css
├── script.js
├── about.html
└── contact.html
```

### 3. Custom MCP Server Integration

Use specialized servers for domain-specific code generation:

```bash
# Quantum circuits
@quantum-ai Generate a quantum circuit for [algorithm]

# Code review and analysis
@ai Review this code for security and performance issues

# Task tracking
@task-complete Mark task complete with summary
```

## Examples

### Example 1: Generate Email Validator

```python
from ai_projects.llm_maker.src.tool_maker import ToolMaker

maker = ToolMaker()
code = maker.create_tool(
    'validate_email',
    'Validates email format using regex',
    {'email': 'str'},
    {'is_valid': 'bool'},
    max_attempts=3
)

# Use the generated code:
exec(code)
print(validate_email('user@example.com'))  # True
```

### Example 2: Generate Data Processing Function

```python
maker = ToolMaker()
code = maker.create_tool(
    'parse_csv_line',
    'Parse a CSV line into a list of values',
    {'line': 'str', 'delimiter': 'str'},
    {'values': 'list'},
    max_attempts=3
)

exec(code)
print(parse_csv_line('a,b,c', ','))  # ['a', 'b', 'c']
```

### Example 3: Generate Static Website

```python
from ai_projects.llm_maker.src.website_maker import WebsiteMaker

maker = WebsiteMaker()
result = maker.create_website(
    'blog-template',
    ['index.html', 'post.html', 'about.html'],
    'A minimalist blog template with dark mode'
)

# Check result
print(result['files'].keys())  # dict_keys(['index.html', 'style.css', ...])

# Write files
for filename, content in result['files'].items():
    with open(f"build/{filename}", 'w') as f:
        f.write(content)
```

## API Reference

### ToolMaker

#### `create_tool(name, description, parameters, returns, max_attempts=3)`

Generate a validated Python function.

**Parameters:**

- `name` (str): Function name
- `description` (str): What the function does
- `parameters` (dict): Input parameters as `{param_name: type_hint_string}`
- `returns` (dict): Return values as `{var_name: type_hint_string}`
- `max_attempts` (int): Max retry attempts on validation failure

**Returns:**

- (str): Complete Python function code with docstring

**Example:**

```python
code = maker.create_tool(
    'reverse_string',
    'Reverses a string',
    {'text': 'str'},
    {'reversed': 'str'}
)
```

### WebsiteMaker

#### `create_website(name, pages, description, style='modern')`

Generate a complete static website.

**Parameters:**

- `name` (str): Project directory name
- `pages` (list): List of HTML filenames to generate
- `description` (str): What the website is for
- `style` (str): Design style ('modern', 'minimal', 'dark', etc.)

**Returns:**

- (dict): `{'name': str, 'files': {filename: content, ...}, 'status': str}`

**Example:**

```python
result = maker.create_website(
    'landing-page',
    ['index.html', 'features.html'],
    'Marketing landing page for SaaS product'
)

for filename, content in result['files'].items():
    print(f"Generated {filename}: {len(content)} bytes")
```

## Safety & Validation

### Banned Imports

The ToolValidator automatically rejects code with these imports:

```
os, sys, subprocess, shutil, pathlib, socket, urllib, requests,
http, pickle, threading, multiprocessing, ctypes, cffi
```

**If generation fails**, the system automatically:

1. Detects the validation error
2. Injects error feedback into next attempt
3. Regenerates safer code
4. Retries up to 3 times by default

### Example: Fixing a Banned Import

**Request (fails):**

```python
code = maker.create_tool(
    'list_files',
    'List files in directory',
    {'path': 'str'},
    {'files': 'list'}
)
# ERROR: os import not allowed
```

**Request (succeeds):**

```python
code = maker.create_tool(
    'extract_numbers',
    'Extract all numbers from text',
    {'text': 'str'},
    {'numbers': 'list'},
    max_attempts=3
)
# Uses regex instead of os/file operations
```

## Integration with Copilot Chat

### Using @llm-maker Agent

In VS Code Copilot Chat:

```
@llm-maker Generate a Python function that converts temperatures from Celsius to Fahrenheit
```

The agent will:

1. Call ToolMaker with appropriate parameters
2. Handle validation failures automatically
3. Return working, validated code
4. Provide usage examples

### Using @ai Agent

For general code generation requests:

```
@ai Create a Python utility function that [description]
```

The agent will:

1. Understand your requirements
2. Route to appropriate code generator
3. Validate safety constraints
4. Return production-ready code

## Common Use Cases

### Use Case 1: Data Validation

```python
maker = ToolMaker()

# Phone number validator
code = maker.create_tool(
    'validate_phone',
    'Validate US phone number format',
    {'phone': 'str'},
    {'is_valid': 'bool'}
)
```

### Use Case 2: Text Processing

```python
# Extract hashtags from text
code = maker.create_tool(
    'extract_hashtags',
    'Extract all hashtags from social media text',
    {'text': 'str'},
    {'hashtags': 'list'}
)
```

### Use Case 3: Mathematical Functions

```python
# Calculate compound interest
code = maker.create_tool(
    'compound_interest',
    'Calculate compound interest',
    {'principal': 'float', 'rate': 'float', 'years': 'float'},
    {'amount': 'float'}
)
```

### Use Case 4: String Utilities

```python
# Generate slug from title
code = maker.create_tool(
    'slugify',
    'Convert title to URL-friendly slug',
    {'title': 'str'},
    {'slug': 'str'}
)
```

### Use Case 5: Static Sites

```python
maker = WebsiteMaker()

# Documentation site
result = maker.create_website(
    'api-docs',
    ['index.html', 'getting-started.html', 'reference.html', 'examples.html'],
    'API documentation with navigation and code examples'
)
```

## Troubleshooting

### Issue: "Import X is not allowed"

**Cause**: The generated code tried to use a banned import

**Solution**: Request a simpler description that doesn't require file/system access

```python
# Instead of: "List files in directory using os module"
# Use: "Filter a list of filenames by extension"
```

### Issue: "Signature mismatch"

**Cause**: Generated function name/parameters don't match spec

**Solution**: Be explicit about parameter names

```python
code = maker.create_tool(
    'my_func',
    'Does X',
    {'input_value': 'str'},  # Exact name matters
    {'output_result': 'str'}
)
```

### Issue: "Code uses eval/exec"

**Cause**: ToolValidator rejected dangerous builtins

**Solution**: Request simpler logic that doesn't need dynamic evaluation

```python
# Instead of: "Parse JSON dynamically"
# Use: "Parse simple key=value format"
```

### Issue: Website generation missing files

**Cause**: Generator failed to create all requested files

**Solution**: Simplify the request or check error logs

```python
result = maker.create_website(
    'simple-site',
    ['index.html'],  # Start with single page
    'A simple single-page site'
)
```

## Advanced Usage

### Custom Retry Logic

```python
from ai_projects.llm_maker.src.tool_maker import ToolMaker

maker = ToolMaker()
code = maker.create_tool(
    'my_function',
    'Does something',
    {'input': 'str'},
    {'output': 'str'},
    max_attempts=5  # Increase retries
)
```

### Batch Generation

```python
functions_to_generate = [
    ('add', 'Add two numbers', {'a': 'int', 'b': 'int'}, {'sum': 'int'}),
    ('multiply', 'Multiply numbers', {'a': 'int', 'b': 'int'}, {'product': 'int'}),
    ('divide', 'Divide two numbers', {'a': 'int', 'b': 'int'}, {'quotient': 'float'}),
]

maker = ToolMaker()
generated_functions = {}

for name, desc, params, returns in functions_to_generate:
    code = maker.create_tool(name, desc, params, returns)
    generated_functions[name] = code
    print(f"Generated {name}")
```

### Validation Before Use

```python
from ai_projects.llm_maker.src.tool_validator import ToolValidator

validator = ToolValidator()
is_valid, errors = validator.validate(generated_code)

if is_valid:
    exec(generated_code)
    print("Code is safe and ready to use")
else:
    print(f"Validation failed: {errors}")
```

## Next Steps

1. **Try it now**: Open Copilot Chat with `Ctrl+Shift+I` and type `@llm-maker Generate a function that [your requirement]`
2. **Learn more**: Check `.github/instructions/llm-maker.instructions.md`
3. **Deep dive**: Review `ai-projects/llm-maker/src/tool_maker.py` source code
4. **Build**: Use generated functions in your Aria features

---

**Start generating safe, validated code with Aria's built-in code generation! 🚀**
