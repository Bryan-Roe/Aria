"""Generate synthetic GitHub Actions training dataset from workflow files.

Creates a dataset suitable for chat fine-tuning about GitHub Actions, CI/CD, and workflows.
Output format:
  datasets/chat/github_actions/train.json  (newline-delimited JSON objects)
  datasets/chat/github_actions/test.json   (newline-delimited JSON objects)
Each line: {"messages": [ {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."} ]}

Design principles:
- Generate Q&A pairs about workflow structure, triggers, jobs, steps
- Include CI/CD best practices and explanations
- Cover common GitHub Actions patterns and use cases
- Deterministic with --seed for reproducibility

Usage:
  python scripts/generate_github_actions_dataset.py --max-records 200
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

DEFAULT_OUTPUT = Path("datasets/chat/github_actions")


@dataclass
class WorkflowInfo:
    name: str
    path: str
    content: str
    parsed_yaml: Dict[str, Any]
    triggers: List[str]
    jobs: List[str]
    uses_actions: List[str]


def parse_workflow(path: Path) -> WorkflowInfo | None:
    """Parse a GitHub Actions workflow file"""
    try:
        content = path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)

        if not isinstance(parsed, dict):
            return None

        # Extract key information
        name = parsed.get("name", path.stem)

        # Extract triggers
        triggers = []
        if "on" in parsed:
            on_config = parsed["on"]
            if isinstance(on_config, str):
                triggers.append(on_config)
            elif isinstance(on_config, list):
                triggers.extend(on_config)
            elif isinstance(on_config, dict):
                triggers.extend(on_config.keys())

        # Extract jobs
        jobs = []
        if "jobs" in parsed and isinstance(parsed["jobs"], dict):
            jobs = list(parsed["jobs"].keys())

        # Extract used actions
        uses_actions = []
        if "jobs" in parsed and isinstance(parsed["jobs"], dict):
            for job_name, job_config in parsed["jobs"].items():
                if isinstance(job_config, dict) and "steps" in job_config:
                    for step in job_config.get("steps", []):
                        if isinstance(step, dict) and "uses" in step:
                            uses_actions.append(step["uses"])

        return WorkflowInfo(
            name=name,
            path=str(path.relative_to(path.parents[2])),  # relative to repo root
            content=content,
            parsed_yaml=parsed,
            triggers=triggers,
            jobs=jobs,
            uses_actions=list(set(uses_actions)),
        )
    except Exception as e:
        print(f"Warning: Could not parse {path}: {e}")
        return None


def generate_workflow_overview_qa(workflow: WorkflowInfo) -> tuple[str, str]:
    """Generate Q&A about workflow overview"""
    user = f"What does the GitHub Actions workflow '{workflow.name}' do?"

    assistant_parts = [f"The workflow '{workflow.name}' is a CI/CD pipeline that:"]

    if workflow.triggers:
        trigger_desc = ", ".join(workflow.triggers)
        assistant_parts.append(f"\n- Triggers on: {trigger_desc}")

    if workflow.jobs:
        job_desc = ", ".join(workflow.jobs)
        assistant_parts.append(f"- Contains {len(workflow.jobs)} job(s): {job_desc}")

    if workflow.uses_actions:
        assistant_parts.append(
            f"- Uses {len(workflow.uses_actions)} different GitHub Actions"
        )

    # Add purpose based on name/jobs
    purpose_hints = {
        "test": "running automated tests",
        "ci": "continuous integration checks",
        "deploy": "deploying code to production or staging",
        "train": "training machine learning models",
        "validate": "validating code quality and correctness",
        "build": "building and compiling the application",
        "lint": "checking code style and quality",
    }

    for keyword, purpose in purpose_hints.items():
        if keyword in workflow.name.lower() or any(
            keyword in job.lower() for job in workflow.jobs
        ):
            assistant_parts.append(
                f"\nThis workflow is primarily focused on {purpose}."
            )
            break

    return user, "\n".join(assistant_parts)


def generate_trigger_qa(workflow: WorkflowInfo) -> tuple[str, str]:
    """Generate Q&A about workflow triggers"""
    user = f"When does the '{workflow.name}' workflow run?"

    if not workflow.triggers:
        return user, "This workflow has no explicit triggers defined."

    assistant_parts = [f"The '{workflow.name}' workflow is triggered by:"]

    trigger_explanations = {
        "push": "code pushes to specified branches",
        "pull_request": "pull request events (opened, synchronized, etc.)",
        "workflow_dispatch": "manual workflow runs via GitHub UI or API",
        "schedule": "scheduled cron jobs at specific times",
        "release": "release events (published, created, etc.)",
        "issues": "issue events (opened, labeled, etc.)",
        "issue_comment": "comments on issues or pull requests",
    }

    for trigger in workflow.triggers:
        explanation = trigger_explanations.get(trigger, f"{trigger} events")
        assistant_parts.append(f"\n- {trigger}: {explanation}")

    # Add schedule details if present
    if "schedule" in workflow.triggers and "on" in workflow.parsed_yaml:
        on_config = workflow.parsed_yaml["on"]
        if isinstance(on_config, dict) and "schedule" in on_config:
            schedule_list = on_config["schedule"]
            if schedule_list and len(schedule_list) > 0:
                cron = schedule_list[0].get("cron", "")
                if cron:
                    assistant_parts.append(f"\nSchedule: {cron}")

    return user, "\n".join(assistant_parts)


def generate_jobs_qa(workflow: WorkflowInfo) -> tuple[str, str]:
    """Generate Q&A about workflow jobs"""
    user = f"What jobs are defined in the '{workflow.name}' workflow?"

    if not workflow.jobs:
        return user, "This workflow has no jobs defined."

    assistant_parts = [f"The workflow defines {len(workflow.jobs)} job(s):\n"]

    jobs_config = workflow.parsed_yaml.get("jobs", {})
    for job_name in workflow.jobs:
        job_config = jobs_config.get(job_name, {})
        assistant_parts.append(f"\n**{job_name}**:")

        # Runner
        runs_on = job_config.get("runs-on", "unknown")
        assistant_parts.append(f"  - Runs on: {runs_on}")

        # Dependencies
        if "needs" in job_config:
            needs = job_config["needs"]
            if isinstance(needs, str):
                assistant_parts.append(f"  - Depends on: {needs}")
            elif isinstance(needs, list):
                assistant_parts.append(f"  - Depends on: {', '.join(needs)}")

        # Steps count
        steps = job_config.get("steps", [])
        assistant_parts.append(f"  - Contains {len(steps)} step(s)")

        # Conditions
        if "if" in job_config:
            assistant_parts.append(f"  - Conditional: {job_config['if']}")

    return user, "\n".join(assistant_parts)


def generate_actions_used_qa(workflow: WorkflowInfo) -> tuple[str, str]:
    """Generate Q&A about actions used in workflow"""
    user = f"What GitHub Actions are used in the '{workflow.name}' workflow?"

    if not workflow.uses_actions:
        return user, "This workflow doesn't use any external GitHub Actions."

    assistant_parts = [
        f"The workflow uses {len(workflow.uses_actions)} different actions:\n"
    ]

    action_descriptions = {
        "actions/checkout": "Checks out the repository code",
        "actions/setup-python": "Sets up a Python environment",
        "actions/setup-node": "Sets up a Node.js environment",
        "actions/upload-artifact": "Uploads build artifacts for later use",
        "actions/download-artifact": "Downloads previously uploaded artifacts",
        "actions/cache": "Caches dependencies to speed up workflows",
        "azure/login": "Authenticates with Azure",
        "azure/cli": "Runs Azure CLI commands",
    }

    for action in sorted(workflow.uses_actions):
        # Extract action name without version
        action_name = action.split("@")[0] if "@" in action else action
        description = action_descriptions.get(
            action_name, f"Performs {action_name} functionality"
        )
        assistant_parts.append(f"- **{action}**: {description}")

    return user, "\n".join(assistant_parts)


def generate_best_practices_qa(workflow: WorkflowInfo) -> tuple[str, str]:
    """Generate Q&A about best practices in the workflow"""
    user = (
        f"What are the best practices demonstrated in the '{workflow.name}' workflow?"
    )

    practices = []

    # Check for specific patterns
    if "actions/checkout" in " ".join(workflow.uses_actions):
        practices.append("- Uses actions/checkout to ensure clean code access")

    if any("cache" in action.lower() for action in workflow.uses_actions):
        practices.append("- Implements caching to improve workflow performance")

    if any("upload-artifact" in action.lower() for action in workflow.uses_actions):
        practices.append("- Preserves build artifacts for debugging and deployment")

    jobs_config = workflow.parsed_yaml.get("jobs", {})
    for job_name, job_config in jobs_config.items():
        if "needs" in job_config:
            practices.append("- Uses job dependencies to create a proper pipeline flow")
            break

    # Check for conditional execution
    for job_name, job_config in jobs_config.items():
        if "if" in job_config:
            practices.append(
                "- Uses conditional job execution to optimize resource usage"
            )
            break

    if "schedule" in workflow.triggers:
        practices.append("- Implements scheduled runs for regular automated tasks")

    if "workflow_dispatch" in workflow.triggers:
        practices.append("- Allows manual workflow triggering for flexibility")

    # Check for matrix strategy
    for job_name, job_config in jobs_config.items():
        if "strategy" in job_config and "matrix" in job_config["strategy"]:
            practices.append(
                "- Uses matrix strategy for testing across multiple configurations"
            )
            break

    if not practices:
        practices.append(
            "- Follows standard GitHub Actions structure with jobs and steps"
        )

    assistant = (
        f"The '{workflow.name}' workflow demonstrates several best practices:\n\n"
        + "\n".join(practices)
    )
    return user, assistant


def generate_modification_qa(workflow: WorkflowInfo) -> tuple[str, str]:
    """Generate Q&A about how to modify the workflow"""
    user = f"How would I modify the '{workflow.name}' workflow to add a new step?"

    assistant = f"""To add a new step to the '{workflow.name}' workflow:

1. Choose which job to modify (available: {', '.join(workflow.jobs) if workflow.jobs else 'none'})
2. Locate the `steps` section within that job
3. Add a new step with:
   - `name`: A descriptive name for the step
   - `run`: Command(s) to execute, or
   - `uses`: An action to use (e.g., actions/checkout@v4)
4. Optionally add conditions with `if:` to control when the step runs

Example step structure:
```yaml
- name: My new step
  run: |
    echo "Running my command"
    python my_script.py
```

Or using an action:
```yaml
- name: Upload results
  uses: actions/upload-artifact@v4
  with:
    name: my-artifact
    path: results/
```

Remember to test your changes in a feature branch before merging to main."""

    return user, assistant


def generate_troubleshooting_qa(workflow: WorkflowInfo) -> tuple[str, str]:
    """Generate Q&A about troubleshooting workflows"""
    user = f"How do I debug failures in the '{workflow.name}' workflow?"

    assistant = f"""To debug failures in the '{workflow.name}' workflow:

1. **Check the Actions tab**: Go to GitHub Actions tab to see run history
2. **Review logs**: Click on the failed run and expand failed steps to see detailed logs
3. **Look for error messages**: Red text usually indicates the failure point
4. **Verify triggers**: Ensure the workflow triggered as expected (check triggers: {', '.join(workflow.triggers) if workflow.triggers else 'none'})
5. **Test locally**: Try running the commands from failed steps on your local machine
6. **Check dependencies**: Ensure all required dependencies are installed
7. **Review permissions**: Verify the workflow has necessary permissions
8. **Use workflow_dispatch**: Add manual trigger for easier testing

Common issues:
- Missing environment variables or secrets
- Incorrect file paths
- Dependency version conflicts
- Insufficient permissions
- Timeout issues (increase with `timeout-minutes`)

For persistent issues, you can enable debug logging by setting these secrets:
- ACTIONS_STEP_DEBUG: true
- ACTIONS_RUNNER_DEBUG: true"""

    return user, assistant


# Template functions for generating Q&A pairs
PROMPT_TEMPLATES = {
    "overview": generate_workflow_overview_qa,
    "triggers": generate_trigger_qa,
    "jobs": generate_jobs_qa,
    "actions": generate_actions_used_qa,
    "best_practices": generate_best_practices_qa,
    "modification": generate_modification_qa,
    "troubleshooting": generate_troubleshooting_qa,
}


def generate_general_qa_pairs() -> List[Dict[str, Any]]:
    """Generate general GitHub Actions Q&A pairs"""
    general_qa = [
        {
            "messages": [
                {"role": "user", "content": "What is GitHub Actions?"},
                {
                    "role": "assistant",
                    "content": "GitHub Actions is a CI/CD (Continuous Integration/Continuous Deployment) platform built into GitHub that allows you to automate your software development workflows. You can:\n\n- Run tests automatically on every push or pull request\n- Build and deploy applications\n- Automate code quality checks and linting\n- Schedule regular tasks\n- Respond to GitHub events (issues, releases, etc.)\n\nWorkflows are defined in YAML files stored in `.github/workflows/` directory.",
                },
            ],
            "source": "general_knowledge",
            "template": "concept",
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What is the structure of a GitHub Actions workflow file?",
                },
                {
                    "role": "assistant",
                    "content": "A GitHub Actions workflow file is a YAML file with the following main sections:\n\n1. **name**: Optional workflow name displayed in the Actions tab\n2. **on**: Defines triggers (push, pull_request, schedule, etc.)\n3. **jobs**: Contains one or more jobs to run\n   - Each job has:\n     - **runs-on**: Runner type (ubuntu-latest, windows-latest, etc.)\n     - **steps**: Sequential actions or commands to execute\n     - **needs**: Optional dependencies on other jobs\n4. **env**: Optional environment variables\n5. **permissions**: Optional permissions settings\n\nExample:\n```yaml\nname: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: npm test\n```",
                },
            ],
            "source": "general_knowledge",
            "template": "structure",
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What are the most common GitHub Actions triggers?",
                },
                {
                    "role": "assistant",
                    "content": "The most common GitHub Actions triggers are:\n\n1. **push**: Triggers on code pushes to specified branches\n   ```yaml\n   on:\n     push:\n       branches: [main, dev]\n   ```\n\n2. **pull_request**: Triggers on PR events (opened, synchronized, etc.)\n   ```yaml\n   on:\n     pull_request:\n       branches: [main]\n   ```\n\n3. **schedule**: Triggers on a cron schedule\n   ```yaml\n   on:\n     schedule:\n       - cron: '0 2 * * *'  # Daily at 2 AM UTC\n   ```\n\n4. **workflow_dispatch**: Allows manual workflow runs\n   ```yaml\n   on:\n     workflow_dispatch:\n       inputs:\n         environment:\n           description: 'Environment to deploy to'\n           required: true\n   ```\n\n5. **release**: Triggers on release events\n   ```yaml\n   on:\n     release:\n       types: [published]\n   ```",
                },
            ],
            "source": "general_knowledge",
            "template": "triggers",
        },
        {
            "messages": [
                {"role": "user", "content": "How do I use secrets in GitHub Actions?"},
                {
                    "role": "assistant",
                    "content": "To use secrets in GitHub Actions:\n\n1. **Add secrets**: Go to repository Settings > Secrets and variables > Actions\n2. **Click 'New repository secret'** and add your secret (e.g., API keys, passwords)\n3. **Reference in workflow**: Use `${{ secrets.SECRET_NAME }}` syntax\n\nExample:\n```yaml\nsteps:\n  - name: Deploy\n    env:\n      API_KEY: ${{ secrets.API_KEY }}\n      DATABASE_URL: ${{ secrets.DATABASE_URL }}\n    run: |\n      echo \"Deploying with credentials...\"\n      ./deploy.sh\n```\n\n**Best practices**:\n- Never commit secrets to code\n- Use environment-specific secrets for dev/staging/prod\n- Secrets are masked in logs\n- Use GitHub's OIDC for cloud provider authentication when possible\n- Consider using environment protection rules for sensitive deployments",
                },
            ],
            "source": "general_knowledge",
            "template": "secrets",
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What is the difference between 'run' and 'uses' in a workflow step?",
                },
                {
                    "role": "assistant",
                    "content": "In GitHub Actions workflow steps:\n\n**run**: Executes shell commands directly\n```yaml\n- name: Install dependencies\n  run: |\n    npm install\n    npm run build\n```\n- Runs arbitrary commands in the runner's shell\n- Can use multiple lines with `|` or `>`\n- Good for simple commands or scripts\n- Has access to environment variables\n\n**uses**: Invokes a reusable action\n```yaml\n- name: Checkout code\n  uses: actions/checkout@v4\n  with:\n    fetch-depth: 0\n```\n- References a pre-built action from GitHub Marketplace or your repository\n- Actions are versioned (using @v4, @main, or commit SHA)\n- Can accept parameters via `with:`\n- Promotes code reuse and maintainability\n- Examples: actions/checkout, actions/setup-python, azure/login\n\n**When to use**:\n- Use `run` for simple commands and scripts\n- Use `uses` for complex operations, third-party integrations, or reusable logic",
                },
            ],
            "source": "general_knowledge",
            "template": "concepts",
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": "How do I run jobs in parallel vs sequentially in GitHub Actions?",
                },
                {
                    "role": "assistant",
                    "content": "GitHub Actions supports both parallel and sequential job execution:\n\n**Parallel (default)**: Jobs run simultaneously by default\n```yaml\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: npm test\n  \n  lint:\n    runs-on: ubuntu-latest\n    steps:\n      - run: npm run lint\n```\nBoth `test` and `lint` run at the same time.\n\n**Sequential**: Use `needs` to create dependencies\n```yaml\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - run: npm build\n  \n  test:\n    needs: build  # Waits for build to complete\n    runs-on: ubuntu-latest\n    steps:\n      - run: npm test\n  \n  deploy:\n    needs: [build, test]  # Waits for both\n    runs-on: ubuntu-latest\n    steps:\n      - run: ./deploy.sh\n```\n\n**Benefits**:\n- Parallel: Faster total execution time\n- Sequential: Ensures correct order (e.g., build before test, test before deploy)\n- Mix both: Some jobs parallel, others sequential",
                },
            ],
            "source": "general_knowledge",
            "template": "parallelism",
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What is a matrix strategy in GitHub Actions?",
                },
                {
                    "role": "assistant",
                    "content": "A matrix strategy in GitHub Actions allows you to run a job with multiple configurations automatically:\n\n```yaml\njobs:\n  test:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python-version: ['3.9', '3.10', '3.11', '3.12']\n        os: [ubuntu-latest, windows-latest, macos-latest]\n    steps:\n      - uses: actions/setup-python@v5\n        with:\n          python-version: ${{ matrix.python-version }}\n      - run: python --version\n      - run: pytest\n```\n\nThis creates 12 jobs (4 Python versions × 3 OS) automatically.\n\n**Key features**:\n- `${{ matrix.variable }}` accesses matrix values\n- `fail-fast: false` continues other jobs if one fails\n- `max-parallel` limits concurrent jobs\n- `include` adds specific combinations\n- `exclude` removes specific combinations\n\n**Use cases**:\n- Testing across multiple Python/Node versions\n- Cross-platform testing (Linux, Windows, macOS)\n- Testing with different dependency versions\n- Different configuration combinations",
                },
            ],
            "source": "general_knowledge",
            "template": "matrix",
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": "How do I cache dependencies in GitHub Actions?",
                },
                {
                    "role": "assistant",
                    "content": "Caching dependencies speeds up workflow runs by reusing previously downloaded packages:\n\n**Using actions/cache**:\n```yaml\nsteps:\n  - uses: actions/checkout@v4\n  \n  - uses: actions/cache@v4\n    with:\n      path: ~/.npm\n      key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}\n      restore-keys: |\n        ${{ runner.os }}-node-\n  \n  - run: npm install\n```\n\n**Language-specific setup actions** with built-in caching:\n```yaml\n# Python with pip cache\n- uses: actions/setup-python@v5\n  with:\n    python-version: '3.11'\n    cache: 'pip'\n\n# Node.js with npm cache\n- uses: actions/setup-node@v4\n  with:\n    node-version: '20'\n    cache: 'npm'\n```\n\n**Benefits**:\n- Reduces workflow time by 30-70%\n- Decreases network load\n- Cache expires after 7 days of no access\n- Maximum cache size: 10 GB per repository\n\n**Best practices**:\n- Use hash of lock files in cache key for version tracking\n- Include OS in key if caching OS-specific files\n- Use restore-keys for partial cache hits",
                },
            ],
            "source": "general_knowledge",
            "template": "caching",
        },
    ]

    return general_qa


def build_records(
    workflows: List[WorkflowInfo], max_records: int, seed: int
) -> List[Dict[str, Any]]:
    """Build Q&A records from workflows"""
    random.seed(seed)
    records: List[Dict[str, Any]] = []

    # Add general Q&A pairs
    general_records = generate_general_qa_pairs()
    records.extend(general_records)

    # Generate workflow-specific Q&A
    for workflow in workflows:
        # Randomize template order per workflow
        template_keys = list(PROMPT_TEMPLATES.keys())
        random.shuffle(template_keys)

        for template_key in template_keys:
            if len(records) >= max_records:
                break

            try:
                template_func = PROMPT_TEMPLATES[template_key]
                user_prompt, assistant_answer = template_func(workflow)

                h = hashlib.sha256(
                    (workflow.name + template_key + assistant_answer[:100]).encode(
                        "utf-8"
                    )
                ).hexdigest()[:16]
                rec = {
                    "messages": [
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": assistant_answer},
                    ],
                    "source_workflow": workflow.name,
                    "source_path": workflow.path,
                    "template": template_key,
                    "hash": h,
                }
                records.append(rec)
            except Exception as e:
                print(
                    f"Warning: Could not generate {template_key} for {workflow.name}: {e}"
                )

        if len(records) >= max_records:
            break

    return records


def write_jsonl(path: Path, records: List[Dict[str, Any]]):
    """Write records to JSONL file"""
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Generate GitHub Actions training dataset")
    ap.add_argument(
        "--workflow-dir",
        default=".github/workflows",
        help="Directory containing workflow files",
    )
    ap.add_argument(
        "--output-dir", default=str(DEFAULT_OUTPUT), help="Output dataset directory"
    )
    ap.add_argument(
        "--max-records",
        type=int,
        default=200,
        help="Maximum total records (train+test)",
    )
    ap.add_argument("--seed", type=int, default=42, help="Random seed")
    ap.add_argument("--train-ratio", type=float, default=0.85, help="Train split ratio")
    args = ap.parse_args()

    # Find repository root (go up from scripts dir)
    repo_root = Path(__file__).resolve().parents[1]
    workflow_dir = repo_root / args.workflow_dir
    out_dir = repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Parse all workflow files
    workflows: List[WorkflowInfo] = []
    if workflow_dir.exists():
        for pattern in ("*.yml", "*.yaml"):
            for workflow_file in workflow_dir.glob(pattern):
                workflow_info = parse_workflow(workflow_file)
                if workflow_info:
                    workflows.append(workflow_info)
                    print(f"Parsed workflow: {workflow_info.name}")

    if not workflows:
        print(f"Warning: No workflow files found in {workflow_dir}")
        print("Generating dataset with only general GitHub Actions Q&A...")

    # Generate Q&A records
    records = build_records(workflows, max_records=args.max_records, seed=args.seed)

    # Train/test split
    random.seed(args.seed)
    random.shuffle(records)
    n_train = int(len(records) * args.train_ratio)
    train_recs = records[:n_train]
    test_recs = records[n_train:] or records[: max(1, len(records) // 10)]

    # Write datasets
    write_jsonl(out_dir / "train.json", train_recs)
    write_jsonl(out_dir / "test.json", test_recs)

    # Write metadata
    meta = {
        "total_records": len(records),
        "train_records": len(train_recs),
        "test_records": len(test_recs),
        "generation_seed": args.seed,
        "workflows_parsed": len(workflows),
        "workflow_names": [w.name for w in workflows],
        "generation_date": datetime.now().isoformat(),
    }
    with (out_dir / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\n{'='*60}")
    print("Dataset generated successfully!")
    print(f"{'='*60}")
    print(json.dumps(meta, indent=2))
    print(f"\nOutput directory: {out_dir}")
    print(f"Train dataset: {out_dir / 'train.json'}")
    print(f"Test dataset: {out_dir / 'test.json'}")


if __name__ == "__main__":
    main()
