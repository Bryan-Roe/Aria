# Aria Automation Runner

Automatically runs core Aria systems and utilities for development and testing.

## Quick Start

### Option 1: Python (Recommended)
```bash
cd c:\Users\Bryan\Aria
python3.14 run_automation.py
```

### Option 2: Windows Batch File
```cmd
cd c:\Users\Bryan\Aria
run_automation.bat
```

### Option 3: PowerShell
```powershell
cd c:\Users\Bryan\Aria
.\run_automation.ps1
```

## What the Automation Does

The automation runner executes the following tasks in sequence:

1. **Environment Validation**
   - Verifies Python version (3.8+)
   - Checks workspace structure
   - Confirms directory availability

2. **Environment Setup Check**
   - Validates all dependencies
   - Checks system configuration
   - Identifies missing components

3. **Test Suite**
   - Runs all pytest tests
   - Reports test results
   - Captures coverage information

4. **Integration Validation**
   - Performs integration checks
   - Validates core systems
   - Generates validation reports

## Features

- **✓ Graceful Shutdown**: Press Ctrl+C to cleanly terminate all processes
- **✓ Comprehensive Logging**: Colored output shows progress and status
- **✓ Error Recovery**: Continues execution even if some tasks have warnings
- **✓ Platform Support**: Works on Windows, macOS, and Linux
- **✓ Extensible**: Easy to add new automation tasks

## Output

The automation runner provides:

- Section headers showing what's running
- Status indicators (✓ success, ✗ error, ⚠ warning, ℹ info)
- Real-time progress updates
- Final status report

## Exit Codes

- `0`: Success - all tasks completed
- `1`: Failure - environment validation failed
- Ctrl+C: Manual interrupt by user

## Requirements

- Python 3.8 or higher
- All dependencies from `requirements.txt` (installed by environment check)
- Standard development tools (git, make, etc.)

## Customization

To extend the automation runner, edit `run_automation.py` and add new methods to the `AutomationRunner` class:

```python
def run_custom_task(self) -> bool:
    """Run a custom automated task."""
    print_section("Running Custom Task")
    
    try:
        # Your automation code here
        print_ok("Custom task completed")
        return True
    except Exception as e:
        print_error(f"Custom task failed: {e}")
        return False
```

Then add the call in the `run()` method.

## Troubleshooting

### Python Not Found
- Ensure Python 3.8+ is installed
- Add Python to your PATH environment variable
- Try using the full path: `C:\Users\Bryan\.local\bin\python3.14.exe run_automation.py`

### Permission Denied
- On Linux/macOS: `chmod +x run_automation.py`
- On Windows: Run Command Prompt as Administrator

### Encoding Errors
- Set environment variable: `PYTHONIOENCODING=utf-8`
- Ensure console supports unicode output

## Integration with CI/CD

The automation runner is designed to work with CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Aria Automation
  run: python3 run_automation.py
```

## Logs and Output

All output is printed to the console. To save logs:

```bash
# On Linux/macOS
python3 run_automation.py | tee automation.log

# On Windows PowerShell
python3.14 run_automation.py | Tee-Object -FilePath automation.log
```

## Related Documentation

- See `scripts/setup_env_check.py` for environment validation details
- See `pytest.ini` for test configuration
- See individual app READMEs for specific system information

## Support

For issues or questions about the automation runner:
1. Check the output messages for specific errors
2. Review the relevant script documentation
3. Consult the main Aria documentation
