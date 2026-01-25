# GitHub Actions Training Dataset

This dataset contains synthetic Q&A pairs for training AI models to understand GitHub Actions, CI/CD workflows, and DevOps best practices.

## Overview

- **Train samples**: 42
- **Test samples**: 8
- **Total samples**: 50
- **Format**: JSONL (newline-delimited JSON)
- **Generated from**: Real workflow files in `.github/workflows/`

## Content

The dataset covers the following topics:

### Workflow-Specific Content
Generated from 6 actual workflows in this repository:
1. **Auto Validation** - Automated validation workflows
2. **E2E + Integration Tests** - End-to-end and integration testing
3. **Aria E2E Tests** - Aria character system tests
4. **QAI CI Pipeline** - Main CI/CD pipeline with validate/train/deploy stages
5. **Quantum Automation** - Quantum computing workflow orchestration
6. **AzureML LoRA Train** - Azure ML model training workflows

### Q&A Templates
For each workflow, the dataset includes:
- **Overview**: What the workflow does and its purpose
- **Triggers**: When and how the workflow runs
- **Jobs**: Detailed job descriptions and dependencies
- **Actions Used**: GitHub Actions and their purposes
- **Best Practices**: CI/CD best practices demonstrated
- **Modification Guide**: How to add or change steps
- **Troubleshooting**: Debugging workflow failures

### General GitHub Actions Knowledge
Includes foundational Q&A pairs about:
- What GitHub Actions is and how it works
- Workflow file structure (YAML format)
- Common triggers (push, pull_request, schedule, etc.)
- Using secrets and environment variables
- Difference between `run` and `uses`
- Parallel vs sequential job execution
- Matrix strategies for testing multiple configurations
- Dependency caching for faster workflows

## File Format

Each line in the JSONL files is a JSON object with this structure:

```json
{
  "messages": [
    {"role": "user", "content": "Question about GitHub Actions"},
    {"role": "assistant", "content": "Detailed answer with examples"}
  ],
  "source_workflow": "Workflow Name",
  "source_path": ".github/workflows/example.yml",
  "template": "overview",
  "hash": "abc123"
}
```

## Generation

This dataset was generated using `scripts/generate_github_actions_dataset.py`:

```bash
python scripts/generate_github_actions_dataset.py --max-records 200
```

To regenerate with different parameters:

```bash
# Generate more samples
python scripts/generate_github_actions_dataset.py --max-records 500

# Use different seed for variation
python scripts/generate_github_actions_dataset.py --seed 123

# Different train/test split
python scripts/generate_github_actions_dataset.py --train-ratio 0.9
```

## Training Usage

This dataset is automatically discovered by the autonomous training orchestrator and can be used with any of the training scripts:

### Quick Training
```bash
# Using the automated pipeline
python scripts/automated_training_pipeline.py --quick --models tinyllama

# Using the aria quick train (adapted for this dataset)
python scripts/aria_quick_train.py
```

### Manual Training with LoRA
```bash
cd AI/microsoft_phi-silica-3.6_v1
python scripts/train_lora.py \
  --dataset ../../datasets/chat/github_actions \
  --hf-model-id TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --epochs 25 \
  --max-train-samples 42 \
  --max-eval-samples 8
```

### Autonomous Training
The dataset is automatically included in autonomous training cycles:

```bash
# Start autonomous training (runs every 30 minutes)
nohup python scripts/autonomous_training_orchestrator.py > data_out/autonomous_training.log 2>&1 &

# Trigger immediate cycle
pkill -USR1 -f autonomous_training
```

## Validation

To validate the dataset:

```bash
# Manual validation
python -c "
import json
with open('datasets/chat/github_actions/train.json') as f:
    samples = [json.loads(line) for line in f]
    print(f'✅ Loaded {len(samples)} valid training samples')
"
```

## Use Cases

This dataset trains models to:
1. **Explain workflows**: Describe what GitHub Actions workflows do
2. **Answer CI/CD questions**: Provide guidance on workflow triggers, jobs, and steps
3. **Debug workflows**: Help troubleshoot common workflow failures
4. **Best practices**: Teach CI/CD best practices and patterns
5. **Modification guidance**: Guide developers on how to extend workflows
6. **General GitHub Actions knowledge**: Understand core concepts like matrix strategies, caching, secrets

## Dataset Quality

✅ **Strengths**:
- Based on real, working workflows from this repository
- Covers diverse CI/CD patterns (testing, training, deployment)
- Includes both specific and general knowledge
- Consistent format compatible with existing training infrastructure
- Multiple question templates for varied learning

⚠️ **Limitations**:
- Limited to 50 samples (can be expanded by adjusting `--max-records`)
- Focused on workflows in this repository (Python, ML, quantum computing)
- May need supplementation with workflows from other domains (e.g., web frontend, mobile)

## Future Enhancements

Potential improvements:
1. Parse more workflow files from other repositories
2. Add examples of advanced GitHub Actions features (reusable workflows, custom actions)
3. Include workflow run history and failure patterns
4. Add examples of GitHub Actions API usage
5. Cover GitHub Actions security best practices
6. Include composite actions and action development

## Related Datasets

Other chat datasets in this repository:
- `app_repo/` - Repository code and documentation
- `aria_movement/` - Aria character movement commands
- `comprehensive/` - Mixed general chat topics
- `dolly/` - Instruction-following dataset

## License

This synthetic dataset is generated from the repository's own workflow files and is part of the Aria project.
