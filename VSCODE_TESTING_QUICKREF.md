# VS Code Testing - Quick Reference

## 🚀 Getting Started

### Open Test Explorer
1. Click the **beaker icon (🧪)** in the Activity Bar (left sidebar)
2. Or press `Ctrl+Shift+T`
3. Tests auto-discover from `tests/` directory

### Run Your First Test
- Click the **▶️ play button** next to any test
- Or right-click test → "Run Test"
- Results appear instantly with ✅ or ❌

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+; Ctrl+A` | Run all tests |
| `Ctrl+; Ctrl+F` | Run failed tests |
| `Ctrl+; Ctrl+L` | Run last test |
| `Ctrl+; Ctrl+D` | Debug last test |

## 🎯 Test Profiles

Quick test configurations accessible from Test Explorer dropdown:

- **Unit Tests (Fast)** - Quick unit tests only (40 tests in ~0.5s)
- **Integration Tests** - External service tests (30 tests in ~3s)
- **All Fast Tests** - Everything except slow/Azure tests (83 tests in ~10s)
- **AutoTrain Tests** - Training orchestrator tests
- **Quantum Tests** - Quantum-specific test files
- **All Tests** - Complete test suite (84+ tests)
- **All with Coverage** - Full suite + coverage report

## 🐛 Debugging Tests

1. Set breakpoints in your code
2. Right-click test → **"Debug Test"**
3. Use Debug toolbar: Step Over (F10), Step Into (F11), Continue (F5)

**Pro Tip:** Test Explorer shows you exactly which line failed with stack traces!

## 📊 View Results

- **Test Output:** Click any test to see stdout/stderr
- **Coverage:** Run with coverage profile, then open `htmlcov/index.html`
- **Filters:** Use Test Explorer search box to find specific tests
- **Test Status:** 
  - ✅ = Passed
  - ❌ = Failed
  - ⏭️ = Skipped
  - 🔄 = Running

## 💡 Pro Tips

1. **Run tests on save:** Tests auto-discover when you save files
2. **Focus on failures:** Click "Run Failed Tests" to re-run only what broke
3. **Use markers:** Filter tests by `unit`, `integration`, `slow`, `azure`
4. **Debug efficiently:** Set breakpoints before debugging tests
5. **Check coverage:** Run coverage profile periodically to find untested code

## 🔧 Troubleshooting

### "No tests found"
1. Click refresh button (🔄) in Test Explorer
2. Check Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"

### Test fails in Test Explorer but passes in terminal
- Verify working directory is set to workspace root
- Check environment variables are exported

### Import errors
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt`

## 📚 More Info

See **VSCODE_TESTING_GUIDE.md** for comprehensive documentation.

---

**Quick Test Commands:**

```powershell
# Using test_runner (recommended)
python .\scripts\test_runner.py --all          # All fast tests
python .\scripts\test_runner.py --unit         # Unit tests only
python .\scripts\test_runner.py --integration  # Integration tests
python .\scripts\test_runner.py --coverage     # With coverage report

# Direct pytest commands
python -m pytest tests/ -v
python -m pytest tests/test_autotrain_unit.py -v
python -m pytest tests/ --cov=scripts --cov=shared --cov-report=html
python -m pytest -m "not slow and not azure" tests/
```
