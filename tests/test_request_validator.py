"""Tests for shared/request_validator.py — centralized request validation helpers."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock

from shared.request_validator import (
    ValidationError,
    parse_json_body,
    validate_fields,
    validate_request,
    CHAT_SCHEMA,
    TTS_SCHEMA,
    QUANTUM_JOB_SCHEMA,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_req(body: dict | None = None, raw: bytes | None = None,
              bad_json: bool = False):
    """Create a mock request object mimicking Azure Functions HttpRequest."""
    req = MagicMock()
    if bad_json:
        req.get_json.side_effect = ValueError("no JSON")
        req.get_body.return_value = b"not-json-at-all!!!"
    elif raw is not None:
        req.get_json.side_effect = ValueError("no JSON")
        req.get_body.return_value = raw
    elif body is not None:
        req.get_json.return_value = body
    else:
        req.get_json.side_effect = ValueError("no JSON")
        req.get_body.return_value = b""
    return req


# ---------------------------------------------------------------------------
# ValidationError
# ---------------------------------------------------------------------------

class TestValidationError:
    def test_stores_message(self):
        err = ValidationError("bad field")
        assert err.message == "bad field"
        assert str(err) == "bad field"

    def test_is_exception(self):
        with pytest.raises(ValidationError):
            raise ValidationError("oops")


# ---------------------------------------------------------------------------
# parse_json_body
# ---------------------------------------------------------------------------

class TestParseJsonBody:
    def test_valid_dict(self):
        req = _make_req(body={"key": "val"})
        body, err = parse_json_body(req)
        assert err is None
        assert body == {"key": "val"}

    def test_empty_body(self):
        req = _make_req()  # get_json raises, get_body returns b""
        body, err = parse_json_body(req)
        assert body is None
        assert err is not None
        assert "Empty" in err

    def test_raw_bytes_fallback(self):
        raw = json.dumps({"fallback": True}).encode()
        req = _make_req(raw=raw)
        body, err = parse_json_body(req)
        assert err is None
        assert body == {"fallback": True}

    def test_invalid_json(self):
        req = _make_req(bad_json=True)
        body, err = parse_json_body(req)
        assert body is None
        assert err is not None
        assert "Invalid JSON" in err

    def test_non_dict_json(self):
        req = MagicMock()
        req.get_json.return_value = ["list", "not", "dict"]
        body, err = parse_json_body(req)
        assert body is None
        assert err is not None
        assert "JSON object" in err

    def test_raw_non_dict(self):
        raw = b'["list"]'
        req = _make_req(raw=raw)
        body, err = parse_json_body(req)
        assert body is None
        assert err is not None
        assert "JSON object" in err


# ---------------------------------------------------------------------------
# validate_fields
# ---------------------------------------------------------------------------

class TestValidateFields:
    def test_required_field_missing(self):
        err = validate_fields({}, {"name": {"type": str, "required": True}})
        assert err is not None
        assert "name" in err

    def test_required_field_present(self):
        err = validate_fields({"name": "Alice"}, {"name": {"type": str, "required": True}})
        assert err is None

    def test_optional_field_absent(self):
        err = validate_fields({}, {"name": {"type": str}})
        assert err is None

    def test_type_mismatch_str(self):
        err = validate_fields({"age": "not-int"}, {"age": {"type": int}})
        assert err is not None
        assert "age" in err

    def test_type_mismatch_list(self):
        err = validate_fields({"items": "string"}, {"items": {"type": list}})
        assert err is not None

    def test_union_type_accepted(self):
        err = validate_fields({"temp": 1}, {"temp": {"type": (int, float)}})
        assert err is None
        err = validate_fields({"temp": 1.5}, {"temp": {"type": (int, float)}})
        assert err is None

    def test_union_type_rejected(self):
        err = validate_fields({"temp": "hot"}, {"temp": {"type": (int, float)}})
        assert err is not None
        assert "|" in err  # shows type union in message

    def test_min_length_string(self):
        err = validate_fields({"msg": ""}, {"msg": {"type": str, "min_length": 1}})
        assert err is not None
        assert "at least" in err

    def test_max_length_string(self):
        err = validate_fields({"msg": "a" * 101}, {"msg": {"type": str, "max_length": 100}})
        assert err is not None
        assert "max length" in err

    def test_min_length_list(self):
        err = validate_fields({"items": []}, {"items": {"type": list, "min_length": 1}})
        assert err is not None

    def test_max_length_list(self):
        err = validate_fields({"items": list(range(11))}, {"items": {"type": list, "max_length": 10}})
        assert err is not None

    def test_min_numeric(self):
        err = validate_fields({"n": -1}, {"n": {"type": int, "min": 0}})
        assert err is not None
        assert ">=" in err

    def test_max_numeric(self):
        err = validate_fields({"n": 101}, {"n": {"type": int, "max": 100}})
        assert err is not None
        assert "<=" in err

    def test_numeric_in_range(self):
        err = validate_fields({"n": 50}, {"n": {"type": int, "min": 0, "max": 100}})
        assert err is None

    def test_allowlist_valid(self):
        err = validate_fields({"role": "user"}, {"role": {"type": str, "allowed": ["user", "admin"]}})
        assert err is None

    def test_allowlist_invalid(self):
        err = validate_fields({"role": "superuser"}, {"role": {"type": str, "allowed": ["user", "admin"]}})
        assert err is not None
        assert "one of" in err

    def test_multiple_fields_first_error_returned(self):
        schema = {
            "a": {"type": str, "required": True},
            "b": {"type": int, "required": True},
        }
        err = validate_fields({}, schema)
        assert err is not None  # one of the required fields missing

    def test_float_passes_union_check(self):
        err = validate_fields({"temp": 0.7}, {"temp": {"type": (int, float), "min": 0, "max": 2}})
        assert err is None


# ---------------------------------------------------------------------------
# validate_request
# ---------------------------------------------------------------------------

class TestValidateRequest:
    def test_valid_request(self):
        req = _make_req(body={"text": "hello", "voice": "en-US"})
        body, err = validate_request(req, TTS_SCHEMA)
        assert err is None
        assert body is not None
        assert body["text"] == "hello"

    def test_invalid_json_propagates(self):
        req = _make_req(bad_json=True)
        body, err = validate_request(req, TTS_SCHEMA)
        assert body is None
        assert err is not None

    def test_missing_required_after_parse(self):
        req = _make_req(body={"voice": "en-US"})  # missing 'text'
        body, err = validate_request(req, TTS_SCHEMA)
        assert err is not None
        assert "text" in err

    def test_body_returned_on_field_error(self):
        req = _make_req(body={"text": ""})  # empty text violates min_length
        body, err = validate_request(req, TTS_SCHEMA)
        assert err is not None
        assert body is not None  # body still returned


# ---------------------------------------------------------------------------
# Pre-built schema smoke tests
# ---------------------------------------------------------------------------

class TestChatSchema:
    def test_valid_minimal(self):
        err = validate_fields(
            {"messages": [{"role": "user", "content": "hi"}]},
            CHAT_SCHEMA,
        )
        assert err is None

    def test_invalid_provider(self):
        err = validate_fields(
            {"messages": [{}], "provider": "unknown_provider"},
            CHAT_SCHEMA,
        )
        assert err is not None
        assert "provider" in err

    def test_temperature_out_of_range(self):
        err = validate_fields({"messages": [{}], "temperature": 5.0}, CHAT_SCHEMA)
        assert err is not None

    def test_empty_messages_list(self):
        err = validate_fields({"messages": []}, CHAT_SCHEMA)
        assert err is not None

    def test_max_output_tokens_too_high(self):
        err = validate_fields({"messages": [{}], "max_output_tokens": 999999}, CHAT_SCHEMA)
        assert err is not None


class TestTTSSchema:
    def test_valid(self):
        err = validate_fields({"text": "Hello world"}, TTS_SCHEMA)
        assert err is None

    def test_too_long(self):
        err = validate_fields({"text": "x" * 5001}, TTS_SCHEMA)
        assert err is not None

    def test_missing_text(self):
        err = validate_fields({}, TTS_SCHEMA)
        assert err is not None


class TestQuantumJobSchema:
    def test_valid(self):
        err = validate_fields({"circuit_type": "bell"}, QUANTUM_JOB_SCHEMA)
        assert err is None

    def test_missing_circuit_type(self):
        err = validate_fields({"shots": 100}, QUANTUM_JOB_SCHEMA)
        assert err is not None

    def test_shots_too_high(self):
        err = validate_fields({"circuit_type": "ghz", "shots": 200000}, QUANTUM_JOB_SCHEMA)
        assert err is not None

    def test_shots_too_low(self):
        err = validate_fields({"circuit_type": "ghz", "shots": 0}, QUANTUM_JOB_SCHEMA)
        assert err is not None
