import os
import json
from pathlib import Path
from scripts.backup_manager import BackupManager

def create_dummy_structure(root: Path):
    (root / 'data_out' / 'lora_training' / 'lora_adapter').mkdir(parents=True, exist_ok=True)
    (root / 'data_out' / 'autotrain').mkdir(parents=True, exist_ok=True)
    (root / 'datasets' / 'chat').mkdir(parents=True, exist_ok=True)

    # Dummy model file
    model_file = root / 'data_out' / 'lora_training' / 'lora_adapter' / 'adapter_config.json'
    model_file.write_text('{"model":"dummy","version":1}')

    # Dummy log file
    log_file = root / 'data_out' / 'autotrain' / 'status.json'
    log_file.write_text('{"status":"completed","final_loss":0.1234}')

    # Dummy dataset file
    dataset_file = root / 'datasets' / 'chat' / 'train.json'
    dataset_file.write_text('[{"messages":[{"role":"user","content":"Hello"}]}]')

    # Config files
    (root / 'autotrain.yaml').write_text('epochs: 1')
    (root / 'quantum_autorun.yaml').write_text('jobs: []')
    (root / 'evaluation_autorun.yaml').write_text('eval: true')
    (root / 'batch_eval_config.yaml').write_text('batch: true')


def test_basic_backup(tmp_path: Path):
    cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        create_dummy_structure(Path('.'))
        manager = BackupManager()
        info = manager.create_backup(include_datasets=False, compress=False, incremental=False)
        assert info['name'].startswith('qai_backup_')
        assert info['changed_files'] > 0
        assert info['unchanged_files'] == 0
        assert info['incremental'] is False
        # Manifest persisted
        manifest = json.loads(Path('backups/backup_manifest.json').read_text())
        assert manifest['backups']
    finally:
        os.chdir(cwd)


def test_incremental_backup(tmp_path: Path):
    cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        create_dummy_structure(Path('.'))
        manager = BackupManager()
        first = manager.create_backup(include_datasets=False, compress=False, incremental=False)
        # Second backup without changes should mark files unchanged
        second = manager.create_backup(include_datasets=False, compress=False, incremental=True)
        assert second['incremental'] is True
        assert second['unchanged_files'] > 0  # All files unchanged
        assert second['changed_files'] == 0
        # Modify one file
        Path('data_out/lora_training/lora_adapter/adapter_config.json').write_text('{"model":"dummy","version":2}')
        third = manager.create_backup(include_datasets=False, compress=False, incremental=True)
        assert third['changed_files'] >= 1
        assert third['unchanged_files'] > 0
    finally:
        os.chdir(cwd)
