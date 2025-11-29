import importlib
from pathlib import Path
import types

def test_submission_gating(monkeypatch, tmp_path):
    mod = importlib.import_module('scripts.azureml_ci_validate')
    # create dummy env with placeholders
    env_path = Path(mod.ROOT) / '.env'
    env_path.write_text('AZURE_ML_SUBSCRIPTION_ID=__REPLACE__\nAZURE_ML_RESOURCE_GROUP=__REPLACE__\nAZURE_ML_WORKSPACE=__REPLACE__\n',encoding='utf-8')
    spec = Path(mod.ROOT)/'.azureml'
    spec.mkdir(exist_ok=True)
    job = spec/'job_dummy.yaml'
    job.write_text('command: echo test\n',encoding='utf-8')
    monkeypatch.setattr(mod,'az_available',lambda: True)
    # Explosion if subprocess.run called; ensure gating returns early
    def fake_run(*a,**k):
        raise AssertionError('subprocess.run should not be invoked due to gating')
    monkeypatch.setattr(importlib.import_module('subprocess'),'run',fake_run)
    assert mod.submit(job) is True