# AutoTrain Test Coverage

Comprehensive test suite for the AutoTrain orchestration system.

## Test Files

### 1. `test_autotrain.py` (Smoke Test)
- **Purpose:** Quick end-to-end validation
- **Coverage:** Default config dry-run, status JSON generation
- **Run time:** < 1 second

### 2. `test_autotrain_unit.py` (Unit Tests)
**24 test cases covering:**

#### Job Dataclass (2 tests)
- Minimal job creation with defaults
- Full job with all parameters

#### YAML Parsing (4 tests)
- YAML file reading
- Single job loading
- Multiple job loading
- Edge case: missing name field

#### HF Command Builder (4 tests)
- Minimal command structure
- Dataset and config parameters
- All override parameters (learning rate, dropout, epochs, samples, seed, model ID, save dir)
- Extra args pass-through

#### Local Command Builder (5 tests)
- Minimal command structure
- Config path handling (basename extraction)
- Samples and epochs parameters
- Reinstall flag
- Ignoring HF-specific parameters

#### Validation (2 tests)
- Dry-run detects missing training scripts
- Dry-run detects missing dataset paths

#### Status JSON (1 test)
- Status collection and structure verification

#### CLI Parsing (1 test)
- List option JSON output

#### Edge Cases (5 tests)
- Empty jobs list
- No jobs key in config
- Null/None values in job config
- Empty extra_args list
- Paths with spaces

### 3. `test_autotrain_integration.py` (Integration Tests)
**14 test cases (excluding 1 slow test):**

#### CLI Invocation (3 tests)
- `--help` option
- `--list` option with JSON validation
- Missing config file error handling

#### Dry Run Mode (3 tests)
- Valid config validation
- Status JSON creation
- Invalid dataset path detection

#### Single Job Execution (2 tests)
- `--job` filter to single job
- Nonexistent job name error

#### Output Structure (2 tests)
- status.json schema validation
- Timestamped run directory creation

#### Multi-Job Execution (1 test)
- Sequential execution of multiple jobs
- Order preservation

#### Error Handling (2 tests)
- Malformed YAML detection
- Missing job name handling

#### Reinstall Flag (1 test)
- `--reinstall` flag passed to local runner

#### Slow Tests (1 test, excluded by default)
- Real execution with log creation

## Running Tests

### All AutoTrain tests (fast)
```powershell
.\venv\Scripts\python.exe -m pytest tests\ -k "autotrain" -v -m "not slow"
```

### Unit tests only
```powershell
.\venv\Scripts\python.exe -m pytest tests\test_autotrain_unit.py -v
```

### Integration tests only
```powershell
.\venv\Scripts\python.exe -m pytest tests\test_autotrain_integration.py -v -m "not slow"
```

### Include slow tests (actual training execution)
```powershell
.\venv\Scripts\python.exe -m pytest tests\ -k "autotrain" -v
```

### Quick smoke test
```powershell
.\venv\Scripts\python.exe -m pytest tests\test_autotrain.py -v
```

## Coverage Summary

| Component | Coverage |
|-----------|----------|
| Job dataclass | ✅ Full |
| YAML parsing | ✅ Full |
| HF command builder | ✅ Full |
| Local command builder | ✅ Full |
| Validation logic | ✅ Core paths |
| Status JSON generation | ✅ Full |
| CLI argument parsing | ✅ Key options |
| Dry-run mode | ✅ Full |
| Multi-job execution | ✅ Sequential flow |
| Error handling | ✅ Common cases |
| Output structure | ✅ Directories and files |

## Test Execution Time

- **Unit tests:** ~0.2s
- **Integration tests (no slow):** ~1.5s
- **Total (excluding slow):** ~1.7s
- **With slow tests:** ~60s (adds real subprocess execution)

## CI/CD Integration

These tests are suitable for:
- Pre-commit hooks (unit tests only)
- Pull request validation (all non-slow tests)
- Nightly builds (all tests including slow)

Example GitHub Actions workflow:
```yaml
- name: Test AutoTrain
  run: |
    python -m pytest tests/ -k "autotrain" -v -m "not slow" --junitxml=test-results.xml
```

## Future Test Improvements

- [ ] Test Azure Blob manifest parsing (requires mock or fixture)
- [ ] Test DeepSpeed config integration
- [ ] Test last_run.json persistence (currently only validates on non-dry-run)
- [ ] Test concurrent job safety (file locking)
- [ ] Test very long job names (path length limits)
- [ ] Test Unicode in job names and dataset paths
- [ ] Performance tests for large job lists
- [ ] Test resume-from checkpoint handling
