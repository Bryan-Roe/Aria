#!/usr/bin/env python
"""
Tests for shared evaluation utilities module.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from evaluation_utils import load_dataset, load_jsonl, naive_predict


def test_load_jsonl():
    """Test loading JSONL files."""
    # Create a temporary JSONL file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"input": "test1", "expected": "output1"}\n')
        f.write('{"input": "test2", "expected": "output2"}\n')
        f.write('{"input": "test3", "expected": "output3"}\n')
        temp_file = Path(f.name)

    try:
        # Test loading all samples
        data = load_jsonl(temp_file)
        assert len(data) == 3
        assert data[0]["input"] == "test1"
        assert data[2]["expected"] == "output3"

        # Test with max_samples
        data = load_jsonl(temp_file, max_samples=2)
        assert len(data) == 2

        print("✓ test_load_jsonl passed")
    finally:
        temp_file.unlink()


def test_load_dataset_json_array():
    """Test loading JSON array format."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(
            [
                {"input": "test1", "expected": "output1"},
                {"input": "test2", "expected": "output2"},
            ],
            f,
        )
        temp_file = Path(f.name)

    try:
        data = load_dataset(temp_file)
        assert len(data) == 2
        assert data[0]["input"] == "test1"

        print("✓ test_load_dataset_json_array passed")
    finally:
        temp_file.unlink()


def test_load_dataset_jsonl():
    """Test loading JSONL format with load_dataset."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"input": "test1"}\n')
        f.write('{"input": "test2"}\n')
        temp_file = Path(f.name)

    try:
        data = load_dataset(temp_file, max_samples=1)
        assert len(data) == 1
        assert data[0]["input"] == "test1"

        print("✓ test_load_dataset_jsonl passed")
    finally:
        temp_file.unlink()


def test_naive_predict_input_field():
    """Test naive_predict with input field."""
    example = {"input": "Hello world"}
    result = naive_predict(example)
    assert result == "echo: Hello world"
    print("✓ test_naive_predict_input_field passed")


def test_naive_predict_messages():
    """Test naive_predict with messages array."""
    example = {
        "messages": [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "4"},
            {"role": "user", "content": "Thanks!"},
        ]
    }
    result = naive_predict(example)
    # Should extract last user message
    assert result == "echo: Thanks!"
    print("✓ test_naive_predict_messages passed")


def test_naive_predict_empty():
    """Test naive_predict with empty input."""
    example = {}
    result = naive_predict(example)
    assert result == "echo:"
    print("✓ test_naive_predict_empty passed")


if __name__ == "__main__":
    test_load_jsonl()
    test_load_dataset_json_array()
    test_load_dataset_jsonl()
    test_naive_predict_input_field()
    test_naive_predict_messages()
    test_naive_predict_empty()
    print("\n✅ All tests passed!")
