# Quick Start: Running Aria Automation

## One-Liner Commands

### Windows Command Prompt

```cmd
cd c:\Users\Bryan\Aria && run_automation.bat
```

### Windows PowerShell

```powershell
cd c:\Users\Bryan\Aria; .\run_automation.ps1
```

### Linux/macOS

```bash
cd ~/Aria && python3 run_automation.py
```

## What Happens

Running the automation will:

1. ✓ Validate your environment
2. ✓ Check all dependencies
3. ✓ Run the test suite
4. ✓ Perform integration validation
5. ✓ Display final status

## Expected Output

```text
═══════════════════════════════════════════════════════════
Environment Validation
═══════════════════════════════════════════════════════════
✓ Python version: 3.14.3
✓ Workspace found: C:\Users\Bryan\Aria
✓ Directory found: scripts/
✓ Directory found: apps/
✓ Directory found: tests/

[... more checks ...]

═══════════════════════════════════════════════════════════
Automation Complete
═══════════════════════════════════════════════════════════
✓ All automated tasks completed successfully!
```

## Troubleshooting

**Python not found?**

- Windows: Use `C:\Users\Bryan\.local\bin\python3.14.exe run_automation.py`
- Linux/macOS: Use `python3` or `python`

**Permission denied?**

- Linux/macOS: Run `chmod +x run_automation.py` first
- Windows: Run Command Prompt as Administrator

**Tests failing?**

- This is normal - the runner continues even with test failures
- Check the test output for details
- Review test logs for specific errors

## Next Steps

- Read `AUTOMATION_RUNNER.md` for detailed documentation
- Check `scripts/setup_env_check.py` for environment details
- Review test suite in `tests/` directory
- See individual app READMEs for system specifics

## Schedule Automated Runs

### Windows Task Scheduler

```cmd
schtasks /create /tn "Aria Automation" /tr "C:\Users\Bryan\Aria\run_automation.bat" /sc daily /st 02:00:00
```

### Linux crontab

```bash
crontab -e
# Add: 0 2 * * * cd ~/Aria && python3 run_automation.py
```

### macOS launchd

Create `~/Library/LaunchAgents/com.aria.automation.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aria.automation</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/username/Aria/run_automation.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

Then load it:

```bash
launchctl load ~/Library/LaunchAgents/com.aria.automation.plist
```

## Support

For more information:

- See `AUTOMATION_RUNNER.md` for full documentation
- Check script headers for technical details
- Review test output for specific issues
