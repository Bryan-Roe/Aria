# Agent Evaluation Project: agent

Evaluate your Microsoft Foundry AI agent locally with pytest-powered testing. This project provides a complete evaluation framework for assessing agent quality, performance, and accuracy using built-in and custom evaluators.

## Overview

This evaluation project enables you to:

- **Run your agent evaluations locally**
- **Measure quality metrics** such as coherence, relevance, etc
- **Create custom evaluators** tailored to your specific requirements
- **Run evaluations in parallel** for faster feedback
- **Submit results to Microsoft Foundry** for centralized tracking and comparison

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Running Evaluations](#running-evaluations)
- [Working with Test Data](#working-with-test-data)
- [Built-in Evaluators](#built-in-evaluators)
- [Custom Evaluators](#custom-evaluators)
- [Viewing Results](#viewing-results)
- [Debugging Evaluators](#debug-evaluators)
- [Submitting to Microsoft Foundry](#submitting-to-microsoft-foundry)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed and configured:

| Requirement            | Description                                                                                                               |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Python 3.10+**       | Python interpreter                                                                                                        |
| **VS Code**            | Visual Studio Code with the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)      |
| **Foundry Toolkit**    | [Foundry Toolkit for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-windows-ai-studio.windows-ai-studio) |
| **Azure CLI**          | Installed and authenticated via `az login`                                                                                |
| **Azure subscription** | With access to Azure AI services and Microsoft Foundry                                                                    |

---

## Quick Start

### Step 1: Set Up Python Environment

1. Use the one-line command below to create Python environment and install dependencies.
    - Windows

        ```powershell
        python -m venv .venv; .\.venv\Scripts\activate; pip install uv; uv pip install -r requirements.txt --prerelease=allow
        ```

    - MacOS / Linux

        ```bash
        python3 -m venv .venv && source .venv/bin/activate && pip install uv && uv pip install -r requirements.txt --prerelease=allow
        ```

2. Select the Python environment in VS Code: Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`), run `Python: Select Interpreter`, and select the new created environment.

### Step 2: Configure Environment Variables

Open the `.env` file and verify your configuration.

### Step 3: Run Your First Evaluation

1. Open the **Testing** panel in VS Code (click the flask icon in the Activity Bar)
2. Click the ▶️ button next to `test_agent.py` to run all tests
3. View results in the Test Results panel

---

## Project Structure

```
agent-eval/
├── test_agent.py    # Main evaluation test file
├── evaluators.py                  # Custom evaluators definitions (prompt templates and code graders)
├── data.jsonl                     # Test dataset (queries and expected outputs)
├── requirements.txt               # Python package dependencies
├── .env                           # Environment variables (API keys, endpoints)
├── pytest.ini                     # Pytest configuration (parallelization, caching)
├── test-results/                  # Local evaluation results (auto-generated)
└── .vscode/
    └── settings.json              # VS Code workspace settings for pytest
```

---

## Configuration

### Environment Variables

The `.env` file contains critical configuration for connecting to Azure services:

| Variable                       | Description                                                   |
| ------------------------------ | ------------------------------------------------------------- |
| `FOUNDRY_PROJECT_ENDPOINT`     | Microsoft Foundry project endpoint where your agent is hosted |
| `AZURE_OPENAI_ENDPOINT`        | Azure OpenAI endpoint for the judge model                     |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Azure OpenAI deployment name for the judge model              |

### Pytest Configuration

The `pytest.ini` file controls test execution behavior:

```ini
[pytest]
# Enable parallel execution
addopts = -n 4
```

To run tests sequentially instead, modify `addopts` to remove `-n 4`.

---

## Running Evaluations

### Using the VS Code Testing Panel

1. **Open Testing Panel**: Click the flask icon in the Activity Bar (left sidebar)
2. **Discover Tests**: VS Code automatically discovers tests in `test_agent.py`
3. **Run All Tests**: Click ▶️ next to the test file name
4. **Run Single Test**: Click ▶️ next to an individual test method
5. **View Output**: Click on a completed test to see detailed results

### Using the Terminal

```bash
# Run all tests
pytest

# Run a specific test
pytest test_agent.py::Test_agent::test_coherence

# Run tests with verbose output
pytest -v

# Run tests sequentially (disable parallel)
pytest -n 0
```

---

## Working with Test Data

### Test Data Format

The `data.jsonl` file contains your test cases in JSON Lines format. Each line represents one test query:

```json
{"id": "query1", "query": "What is the weather in Seattle?"}
{"id": "query2", "query": "Book a meeting for tomorrow", "ground_truth": "Meeting scheduled"}
```

| Field          | Required | Description                                               |
| -------------- | -------- | --------------------------------------------------------- |
| `id`           | Yes      | Unique identifier for the test case                       |
| `query`        | Yes      | The input query to send to your agent                     |
| `ground_truth` | No       | Expected response (required for some built-in evaluators) |

### Generate Test Cases with GitHub Copilot

Foundry Toolkit provides CodeLens integration to help you generate test data:

1. Open `data.jsonl` in VS Code
2. Click **"✨ Generate Test Cases with Copilot"** at the top of the file
3. Copilot will analyze your agent and suggest relevant test cases
4. Review and customize the generated data as needed

---

## Built-in Evaluators

This project includes several pre-configured evaluators through `BuiltInEvaluatorConfig`. To see the complete list of available built-in evaluators, hover over `BuiltInEvaluatorConfig` in your test file—VS Code's IntelliSense will display all supported evaluator options along with their descriptions.

## Custom Evaluators

Create evaluators tailored to your specific requirements using prompts or code.

### Custom Prompt Evaluator

Define an LLM-based evaluator using a natural language prompt:

```python
from pytest_agent_evals import CustomPromptEvaluatorConfig

custom_prompt = """
You are evaluating whether the agent's response is professional and courteous.
Score from 1 (unprofessional) to 5 (highly professional).

Query:
Response:

Output JSON only: {"result": <score>, "reason": "<explanation>"}
"""


@evals.evaluator(CustomPromptEvaluatorConfig(name="professionalism", prompt=custom_prompt, threshold=3))
def test_professionalism(self, evaluator_results: EvaluatorResults):
    assert evaluator_results.professionalism.result == "pass"
```

### Custom Code Evaluator

Implement evaluation logic in Python for deterministic checks:

```python
from pytest_agent_evals import CustomCodeEvaluatorConfig


def check_response_length(sample: dict, item: dict) -> float:
    """Check if response meets minimum length requirements."""
    response = sample.get("output_text", "")
    min_length = 50
    return 1.0 if len(response) >= min_length else 0.0


@evals.evaluator(CustomCodeEvaluatorConfig(name="response_length", grader=check_response_length, threshold=0.5))
def test_response_length(self, evaluator_results: EvaluatorResults):
    assert evaluator_results.response_length.result == "pass"
```

### Add or Update Custom Evaluators with GitHub Copilot

1. Open `test_agent.py` in VS Code
2. Look for the **"+ Add Custom Evaluator with Copilot"** CodeLens (above the test class) and the **"✨ Update Custom Evaluator with Copilot"** CodeLens (above the test function)
3. Describe your evaluation criteria in natural language
4. Copilot generates the evaluator code for you

---

## Viewing Results

### Local Results

After running evaluations, results are saved to the `test-results/` folder:

- **JSON Results**: Detailed metrics and scores for each test case
- **Test Output**: Console output from pytest showing pass/fail status

### Accessing Results in VS Code

1. **Testing Panel**: Click on any test to view its output in the bottom panel
2. **Foundry Toolkit Panel**: Navigate to **FOUNDRY TOOLKIT** > **Local Evaluation Results** to browse saved results
3. **File Explorer**: Open files in `test-results/` directly

### Results Schema

```json
{
    "rows": [
        {
            "inputs.query": "...",
            "outputs.coherence": 4,
            "outputs.relevance": 5
        }
    ]
}
```

---

## Debugging Evaluators

When some test cases failed, you can debug the specific case by clicking the "Debug Test" icon next to an individual test case in Test Explorer. By setting breakpoints in your test function (as well as the custom code evaluator function), you can see the intermediate states.

---

## Submitting to Microsoft Foundry

Upload your local evaluation results to Microsoft Foundry for centralized tracking, comparison, and collaboration.

### How to Submit

1. Open the **Foundry Toolkit** panel in VS Code
2. Navigate to your evaluation results under **Local Evaluation Results**
3. Click **"Submit Evaluation to Foundry"**
4. Confirm the target project and model deployment
5. View your results in the Foundry portal

### Benefits of Foundry Submission

- **Centralized Dashboard**: Track evaluation history across all team members
- **Version Comparison**: Compare results across different agent versions
- **Collaboration**: Share evaluation insights with your team
- **Audit Trail**: Maintain records for compliance and quality assurance

---

## Troubleshooting

### Common Issues

| Issue                          | Solution                                                                                  |
| ------------------------------ | ----------------------------------------------------------------------------------------- |
| **Tests not discovered**       | Ensure `pytest` is configured in VS Code settings and the Python environment is activated |
| **Authentication errors**      | Run `az login` to authenticate with Azure CLI                                             |
| **Model deployment not found** | Verify `AZURE_OPENAI_DEPLOYMENT_NAME` matches your deployment in Azure Portal             |
| **Agent not found**            | Confirm the agent exists in your Foundry project at `FOUNDRY_PROJECT_ENDPOINT`            |
| **Timeout errors**             | Increase timeout in pytest.ini or reduce parallel workers with `-n 2`                     |

### Debugging Tips

1. **Check Python Environment**: Verify the correct environment is activated
2. **Validate .env File**: Ensure all variables are set correctly
3. **Review Logs**: Check the Output panel in VS Code for detailed error messages
4. **Run Verbose Mode**: Execute `pytest -v --tb=long` for detailed tracebacks

### Getting Help

- **Foundry Toolkit Documentation**: [View Docs](https://aka.ms/AIToolkit/doc/eval)
- **GitHub Issues**: Report bugs at the [Foundry Toolkit repository](https://github.com/microsoft/vscode-ai-toolkit)

---
