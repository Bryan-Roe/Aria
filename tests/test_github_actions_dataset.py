"""Test GitHub Actions dataset generation and validation."""
import json
import pytest
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = REPO_ROOT / "datasets" / "chat" / "github_actions"
TRAIN_FILE = DATASET_DIR / "train.json"
TEST_FILE = DATASET_DIR / "test.json"
METADATA_FILE = DATASET_DIR / "metadata.json"
GENERATOR_SCRIPT = REPO_ROOT / "scripts" / "generate_github_actions_dataset.py"


def test_dataset_files_exist():
    """Test that all required dataset files exist."""
    assert DATASET_DIR.exists(), f"Dataset directory not found: {DATASET_DIR}"
    assert TRAIN_FILE.exists(), f"Train file not found: {TRAIN_FILE}"
    assert TEST_FILE.exists(), f"Test file not found: {TEST_FILE}"
    assert METADATA_FILE.exists(), f"Metadata file not found: {METADATA_FILE}"


def test_train_dataset_format():
    """Test that train dataset has correct format."""
    with open(TRAIN_FILE) as f:
        samples = [json.loads(line) for line in f]
    
    assert len(samples) > 0, "Train dataset is empty"
    
    for i, sample in enumerate(samples):
        assert "messages" in sample, f"Sample {i} missing 'messages' field"
        assert isinstance(sample["messages"], list), f"Sample {i} 'messages' is not a list"
        assert len(sample["messages"]) >= 2, f"Sample {i} needs at least 2 messages"
        
        # Check first message is from user
        assert sample["messages"][0]["role"] == "user", f"Sample {i} first message should be from user"
        assert "content" in sample["messages"][0], f"Sample {i} first message missing content"
        
        # Check second message is from assistant
        assert sample["messages"][1]["role"] == "assistant", f"Sample {i} second message should be from assistant"
        assert "content" in sample["messages"][1], f"Sample {i} second message missing content"


def test_test_dataset_format():
    """Test that test dataset has correct format."""
    with open(TEST_FILE) as f:
        samples = [json.loads(line) for line in f]
    
    assert len(samples) > 0, "Test dataset is empty"
    
    for i, sample in enumerate(samples):
        assert "messages" in sample, f"Sample {i} missing 'messages' field"
        assert isinstance(sample["messages"], list), f"Sample {i} 'messages' is not a list"
        assert len(sample["messages"]) >= 2, f"Sample {i} needs at least 2 messages"


def test_metadata_content():
    """Test that metadata contains expected fields."""
    with open(METADATA_FILE) as f:
        metadata = json.load(f)
    
    assert "total_records" in metadata
    assert "train_records" in metadata
    assert "test_records" in metadata
    assert "generation_seed" in metadata
    assert "workflows_parsed" in metadata
    
    # Verify counts match actual files
    with open(TRAIN_FILE) as f:
        train_count = sum(1 for _ in f)
    with open(TEST_FILE) as f:
        test_count = sum(1 for _ in f)
    
    assert metadata["train_records"] == train_count, "Metadata train count mismatch"
    assert metadata["test_records"] == test_count, "Metadata test count mismatch"
    assert metadata["total_records"] == train_count + test_count, "Metadata total count mismatch"


def test_dataset_content_quality():
    """Test that dataset contains meaningful content."""
    with open(TRAIN_FILE) as f:
        samples = [json.loads(line) for line in f]
    
    # Check that questions and answers are substantive
    for i, sample in enumerate(samples[:10]):  # Check first 10 samples
        user_content = sample["messages"][0]["content"]
        assistant_content = sample["messages"][1]["content"]
        
        # Questions should be at least 10 characters
        assert len(user_content) >= 10, f"Sample {i} question too short"
        
        # Answers should be at least 20 characters
        assert len(assistant_content) >= 20, f"Sample {i} answer too short"
        
        # Check for GitHub Actions related keywords in the dataset
        combined = (user_content + " " + assistant_content).lower()
        github_keywords = ["workflow", "github", "action", "job", "step", "trigger", "ci", "cd"]
        has_keyword = any(keyword in combined for keyword in github_keywords)
        assert has_keyword, f"Sample {i} doesn't appear to be about GitHub Actions"


def test_dataset_diversity():
    """Test that dataset covers multiple templates/topics."""
    with open(TRAIN_FILE) as f:
        samples = [json.loads(line) for line in f]
    
    templates = set()
    for sample in samples:
        if "template" in sample:
            templates.add(sample["template"])
    
    # Should have at least 5 different templates
    assert len(templates) >= 5, f"Dataset should have diverse templates, found: {templates}"


def test_generator_script_exists():
    """Test that the generator script exists and is executable."""
    assert GENERATOR_SCRIPT.exists(), f"Generator script not found: {GENERATOR_SCRIPT}"


@pytest.mark.slow
def test_dataset_regeneration():
    """Test that dataset can be regenerated successfully."""
    # Run the generator with a small number of records for quick test
    result = subprocess.run(
        [sys.executable, str(GENERATOR_SCRIPT), "--max-records", "20", "--seed", "99"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    assert result.returncode == 0, f"Generator failed: {result.stderr}"
    assert "Dataset generated successfully" in result.stdout
    
    # Verify files still exist and are valid
    assert TRAIN_FILE.exists()
    assert TEST_FILE.exists()
    with open(TRAIN_FILE) as f:
        samples = [json.loads(line) for line in f]
    assert len(samples) > 0


def test_no_duplicate_hashes():
    """Test that samples have unique hashes (no exact duplicates)."""
    with open(TRAIN_FILE) as f:
        train_samples = [json.loads(line) for line in f]
    with open(TEST_FILE) as f:
        test_samples = [json.loads(line) for line in f]
    
    all_samples = train_samples + test_samples
    hashes = [s.get("hash") for s in all_samples if "hash" in s]
    
    # Should have no duplicate hashes
    assert len(hashes) == len(set(hashes)), "Found duplicate hashes in dataset"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
