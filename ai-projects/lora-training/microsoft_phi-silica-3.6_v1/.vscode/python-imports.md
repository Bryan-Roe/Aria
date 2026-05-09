# Python Import Resolution for VS Code

This directory contains Python scripts that require ML/AI packages. If you see import errors in the editor:

## Quick Fix

1. Ensure the virtual environment is activated and packages are installed:

   ```powershell
   cd AI\microsoft_phi-silica-3.6_v1
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Select the correct Python interpreter in VS Code:
   - Press `Ctrl+Shift+P`
   - Type "Python: Select Interpreter"
   - Choose `.venv\Scripts\python.exe` from this directory

3. Restart the Python Language Server:
   - Press `Ctrl+Shift+P`
   - Type "Python: Restart Language Server"

## Import Errors Are Expected Without Installation

The `train_lora.py` script uses try/except blocks to gracefully handle missing imports:

```python
try:
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model
except Exception:
    # Allows dry-run mode without installing packages
    load_dataset = None
    AutoModelForCausalLM = None
    # etc.
```

This allows you to:

- Run `--dry-run` validation without installing ML packages
- Explore code structure without downloading multi-GB dependencies
- Install packages only when ready for actual training

## VS Code Settings (Optional)

If you frequently work in this directory, add to `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/AI/microsoft_phi-silica-3.6_v1/venv/Scripts/python.exe",
  "python.analysis.extraPaths": [
    "${workspaceFolder}/AI/microsoft_phi-silica-3.6_v1/venv/Lib/site-packages"
  ]
}
```

This will automatically resolve imports once packages are installed in the venv.
