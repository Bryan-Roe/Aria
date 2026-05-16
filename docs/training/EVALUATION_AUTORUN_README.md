# Evaluation AutoRun Orchestrator

**Automated AI model evaluation** following the same orchestration pattern as `autotrain.py` and `quantum_autorun.py`.

## Quick Start

```powershell
# Validate configuration (dry-run)
python .\scripts\evaluation_autorun.py --dry-run

# List all configured jobs
python .\scripts\evaluation_autorun.py --list

# Run a specific evaluation job
python .\scripts\evaluation_autorun.py --job eval_smoke_test

# Run all enabled evaluation jobs
python .\scripts\evaluation_autorun.py
```

## Architecture

### YAML-Driven Configuration (`evaluation_autorun.yaml`)

Define evaluation jobs with:

- **Model types**: `lora`, `azure`, `openai`, `local`, `quantum`
- **Datasets**: Path to test dataset
- **Metrics**: Configurable evaluation metrics per model type
- **Output formats**: JSON, CSV, or Markdown

### Supported Model Types & Metrics

| Model Type | Metrics | Requirements |
| ------------ | --------- | -------------- |
| `lora` | accuracy, bleu, rouge, response_time, token_efficiency | LoRA adapter path |
| `azure` | accuracy, bleu, rouge, response_time, cost_per_token | Azure OpenAI credentials |
| `openai` | accuracy, bleu, rouge, response_time, cost_per_token | OpenAI API key |
| `local` | response_time, determinism, rule_coverage | None (offline) |
| `quantum` | accuracy, precision, recall, f1_score, circuit_depth | Quantum model results |

### Output Structure

```text
data_out/evaluation_autorun/
├── status.json                              # Global summary
├── <job_name>/
│   ├── last_run.json                        # Latest run metadata
│   └── <timestamp>/
│       ├── results.json                     # Evaluation results
│       └── stdout.log                       # Full execution log
```

## Configuration Examples

### LoRA Model Evaluation

```yaml
- name: eval_lora_phi35
  enabled: true
  model_type: lora
  model_path: data_out/lora_training/phi35
  dataset: datasets/chat/dolly
  max_samples: 100
  metrics:
    - accuracy
    - bleu
    - rouge
    - response_time
  output_format: json
  save_results: true
  batch_size: 4
```

### Azure OpenAI Baseline

```yaml
- name: eval_azure_baseline
  enabled: true
  model_type: azure
  azure_deployment: gpt-4o-mini
  dataset: datasets/chat/mixed_chat
  max_samples: 50
  metrics:
    - accuracy
    - response_time
    - cost_per_token
  output_format: json
```

### Quantum Classifier Evaluation

```yaml
- name: eval_quantum_heart
  enabled: true
  model_type: quantum
  model_path: ai-projects/quantum-ml/results/heart_disease_model.json
  dataset: datasets/quantum/heart_disease.csv
  max_samples: null  # Full test set
  metrics:
    - accuracy
    - precision
    - recall
    - f1_score
  output_format: json
```

### Local Provider (Free/Offline)

```yaml
- name: eval_local_baseline
  enabled: true
  model_type: local
  dataset: datasets/chat/mixed_chat
  max_samples: 20
  metrics:
    - response_time
    - determinism
  output_format: json
```

## Execution Modes

### Dry-Run (Validation Only)

```powershell
python .\scripts\evaluation_autorun.py --dry-run
```

**Output**: Validates configuration, checks paths, prints commands without execution.

### Single Job Execution

```powershell
python .\scripts\evaluation_autorun.py --job eval_smoke_test
```

**Output**: Runs only the specified job, writes results and logs.

### All Jobs

```powershell
python .\scripts\evaluation_autorun.py
```

**Output**: Runs all enabled jobs sequentially, aggregates status.

### List Jobs

```powershell
python .\scripts\evaluation_autorun.py --list
```

**Output**: JSON array of all configured jobs with their parameters.

## Status JSON Schema

```json
{
  "generated_at": "2025-11-22T17:30:00Z",
  "total_jobs": 5,
  "succeeded": 3,
  "failed": 0,
  "validated": 2,
  "missing": 0,
  "jobs": [
    {
      "name": "eval_smoke_test",
      "model_type": "lora",
      "cmd": ["python", "..."],
      "start_time": "20251122T173000Z",
      "status": "succeeded",
      "return_code": 0,
      "duration_sec": 12.5,
      "log": "data_out/.../stdout.log",
      "results_file": "data_out/.../results.json",
      "metrics_computed": ["accuracy", "response_time"],
      "evaluation_summary": {
        "accuracy": 0.85,
        "avg_response_time_ms": 234
      }
    }
  ]
}
```

## VS Code Tasks

Add to `.vscode/tasks.json`:

```json
{
  "label": "Run: Evaluation AutoRun (dry-run)",
  "type": "shell",
  "options": { "cwd": "${workspaceFolder}" },
  "command": "python",
  "args": [".\\scripts\\evaluation_autorun.py", "--dry-run"],
  "isBackground": false
},
{
  "label": "Run: Evaluation AutoRun (all)",
  "type": "shell",
  "options": { "cwd": "${workspaceFolder}" },
  "command": "python",
  "args": [".\\scripts\\evaluation_autorun.py"],
  "isBackground": false
}
```

## Environment Variables

### Azure OpenAI (for `model_type: azure`)

```powershell
$env:AZURE_OPENAI_API_KEY = "your-key"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
$env:AZURE_OPENAI_API_VERSION = "2024-08-01-preview"
```

### OpenAI (for `model_type: openai`)

```powershell
$env:OPENAI_API_KEY = "your-key"
$env:OPENAI_MODEL = "gpt-4o-mini"  # Optional
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run evaluation suite
  run: |
    python scripts/evaluation/evaluation_autorun.py --dry-run
    python scripts/evaluation/evaluation_autorun.py --job eval_smoke_test

- name: Upload evaluation results
  uses: actions/upload-artifact@v3
  with:
    name: evaluation-results
    path: data_out/evaluation_autorun/
```

### Azure Pipelines Example

```yaml
- script: python scripts/evaluation/evaluation_autorun.py --dry-run
  displayName: 'Validate evaluation config'

- script: python scripts/evaluation/evaluation_autorun.py
  displayName: 'Run evaluation suite'

- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: 'data_out/evaluation_autorun'
    artifactName: 'evaluation-results'
```

## Design Patterns Used

✅ **YAML-driven declarative config** - Single source of truth for evaluation jobs
✅ **Sequential execution** - Jobs run in order with clear progress tracking
✅ **Dry-run validation** - Check paths and config before execution
✅ **Machine-readable status** - JSON output for automation
✅ **Timestamped runs** - No overwrites, full audit trail
✅ **Project venv isolation** - Uses correct Python environment per domain
✅ **Modular evaluation scripts** - One script per model type
✅ **Flexible metrics** - Configurable per job and model type

## Extending the Orchestrator

### Adding a New Model Type

1. **Create evaluation script**: `scripts/evaluate_<model_type>_model.py`
2. **Add to `EVAL_SCRIPTS` dict** in `evaluation_autorun.py`
3. **Define supported metrics** in `SUPPORTED_METRICS` dict
4. **Update YAML examples** in this README

### Adding a New Metric

1. **Implement in evaluation script** for relevant model types
2. **Add to `SUPPORTED_METRICS`** for those model types
3. **Document in README** with usage examples

### Custom Output Formats

Evaluation scripts should support:

- `--output-format json` (default)
- `--output-format csv` (for spreadsheet analysis)
- `--output-format markdown` (for reports)

## Troubleshooting

### "Config not found" Error

```powershell
# Specify config path explicitly
python .\scripts\evaluation_autorun.py --config .\path\to\evaluation_autorun.yaml
```

### Missing Dependencies

```powershell
# Install evaluation dependencies
pip install -r requirements.txt
pip install nltk rouge-score  # For NLP metrics
```

### Azure Authentication Failures

```powershell
# Verify environment variables
echo $env:AZURE_OPENAI_API_KEY
echo $env:AZURE_OPENAI_ENDPOINT

# Check endpoint format (must include https://)
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
```

### Evaluation Script Not Found

Current limitation: Evaluation scripts need to be created per model type. The orchestrator validates their existence during dry-run. If scripts don't exist yet, you'll see warnings but the orchestrator will still validate the configuration.

## Next Steps

1. **Implement evaluation scripts** in `scripts/evaluate_*_model.py`
2. **Add VS Code tasks** for quick evaluation runs
3. **Integrate with CI/CD** for automated regression testing
4. **Create comparison reports** across model types
5. **Add visualization** for evaluation results

## Related Documentation

- `AUTOTRAIN_README.md` - ML training orchestrator
- `QUANTUM_AUTORUN_README.md` - Quantum training orchestrator
- `AI_DATASETS_CATALOG.md` - Dataset reference
- `QUICK_REFERENCE.md` - All orchestrators overview
