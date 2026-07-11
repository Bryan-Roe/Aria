"""Tests for AGI and subscription schemas in shared/request_validator.py.

Covers schemas not exercised by test_request_validator.py:
- AGI_BASE_SCHEMA (query/messages/model/temperature/max_output_tokens/verbose)
- AGI_REASON_SCHEMA (goals, include_reasoning_summary)
- AGI_STREAM_SCHEMA (inherits AGI_REASON_SCHEMA)
- SUBSCRIPTION_SCHEMA (user_id/tier)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.request_validator import (
    AGI_ANALYZE_SCHEMA,
    AGI_BASE_SCHEMA,
    AGI_REASON_SCHEMA,
    AGI_STREAM_SCHEMA,
    SUBSCRIPTION_SCHEMA,
    validate_fields,
)

# ---------------------------------------------------------------------------
# AGI_BASE_SCHEMA
# ---------------------------------------------------------------------------


class TestAgiBaseSchema:
    def test_all_optional_fields_absent_is_valid(self):
        err = validate_fields({}, AGI_BASE_SCHEMA)
        assert err is None

    def test_query_string_valid(self):
        err = validate_fields({"query": "What is AI?"}, AGI_BASE_SCHEMA)
        assert err is None

    def test_query_too_long_invalid(self):
        err = validate_fields({"query": "x" * 10001}, AGI_BASE_SCHEMA)
        assert err is not None
        assert "query" in err

    def test_messages_list_valid(self):
        err = validate_fields({"messages": [{"role": "user", "content": "hi"}]}, AGI_BASE_SCHEMA)
        assert err is None

    def test_messages_too_many_invalid(self):
        err = validate_fields({"messages": [{}] * 501}, AGI_BASE_SCHEMA)
        assert err is not None

    def test_model_string_valid(self):
        err = validate_fields({"model": "gpt-4o"}, AGI_BASE_SCHEMA)
        assert err is None

    def test_model_too_long_invalid(self):
        err = validate_fields({"model": "m" * 257}, AGI_BASE_SCHEMA)
        assert err is not None
        assert "model" in err

    def test_temperature_valid_float(self):
        err = validate_fields({"temperature": 0.7}, AGI_BASE_SCHEMA)
        assert err is None

    def test_temperature_zero_valid(self):
        err = validate_fields({"temperature": 0}, AGI_BASE_SCHEMA)
        assert err is None

    def test_temperature_two_valid(self):
        err = validate_fields({"temperature": 2}, AGI_BASE_SCHEMA)
        assert err is None

    def test_temperature_below_min_invalid(self):
        err = validate_fields({"temperature": -0.1}, AGI_BASE_SCHEMA)
        assert err is not None

    def test_temperature_above_max_invalid(self):
        err = validate_fields({"temperature": 2.1}, AGI_BASE_SCHEMA)
        assert err is not None

    def test_temperature_bool_rejected(self):
        err = validate_fields({"temperature": True}, AGI_BASE_SCHEMA)
        assert err is not None

    def test_max_output_tokens_valid(self):
        err = validate_fields({"max_output_tokens": 1024}, AGI_BASE_SCHEMA)
        assert err is None

    def test_max_output_tokens_min_boundary(self):
        err = validate_fields({"max_output_tokens": 1}, AGI_BASE_SCHEMA)
        assert err is None

    def test_max_output_tokens_max_boundary(self):
        err = validate_fields({"max_output_tokens": 128000}, AGI_BASE_SCHEMA)
        assert err is None

    def test_max_output_tokens_zero_invalid(self):
        err = validate_fields({"max_output_tokens": 0}, AGI_BASE_SCHEMA)
        assert err is not None

    def test_max_output_tokens_over_max_invalid(self):
        err = validate_fields({"max_output_tokens": 128001}, AGI_BASE_SCHEMA)
        assert err is not None

    def test_verbose_bool_valid(self):
        err = validate_fields({"verbose": True}, AGI_BASE_SCHEMA)
        assert err is None
        err = validate_fields({"verbose": False}, AGI_BASE_SCHEMA)
        assert err is None

    def test_verbose_non_bool_invalid(self):
        err = validate_fields({"verbose": 1}, AGI_BASE_SCHEMA)
        assert err is not None

    def test_combined_valid_fields(self):
        err = validate_fields(
            {
                "query": "Summarize the code",
                "model": "gpt-4o",
                "temperature": 0.5,
                "max_output_tokens": 2048,
                "verbose": False,
            },
            AGI_BASE_SCHEMA,
        )
        assert err is None


# ---------------------------------------------------------------------------
# AGI_REASON_SCHEMA
# ---------------------------------------------------------------------------


class TestAgiReasonSchema:
    def test_inherits_base_fields(self):
        # Base fields should still work
        err = validate_fields({"query": "Analyze this", "temperature": 0.8}, AGI_REASON_SCHEMA)
        assert err is None

    def test_goals_list_valid(self):
        err = validate_fields({"goals": ["goal1", "goal2"]}, AGI_REASON_SCHEMA)
        assert err is None

    def test_goals_too_many_invalid(self):
        err = validate_fields({"goals": [f"goal{i}" for i in range(11)]}, AGI_REASON_SCHEMA)
        assert err is not None
        assert "goals" in err

    def test_goals_exactly_ten_valid(self):
        err = validate_fields({"goals": [f"goal{i}" for i in range(10)]}, AGI_REASON_SCHEMA)
        assert err is None

    def test_goals_empty_list_valid(self):
        err = validate_fields({"goals": []}, AGI_REASON_SCHEMA)
        assert err is None

    def test_goals_absent_valid(self):
        err = validate_fields({}, AGI_REASON_SCHEMA)
        assert err is None

    def test_include_reasoning_summary_bool_valid(self):
        err = validate_fields({"include_reasoning_summary": True}, AGI_REASON_SCHEMA)
        assert err is None

    def test_include_reasoning_summary_non_bool_invalid(self):
        err = validate_fields({"include_reasoning_summary": "yes"}, AGI_REASON_SCHEMA)
        assert err is not None

    def test_combined_reason_fields_valid(self):
        err = validate_fields(
            {
                "query": "Plan the implementation",
                "goals": ["Correctness", "Performance"],
                "include_reasoning_summary": True,
                "temperature": 0.3,
            },
            AGI_REASON_SCHEMA,
        )
        assert err is None


# ---------------------------------------------------------------------------
# AGI_STREAM_SCHEMA (should be identical to or superset of AGI_REASON_SCHEMA)
# ---------------------------------------------------------------------------


class TestAgiStreamSchema:
    def test_has_same_keys_as_reason_schema(self):
        # AGI_STREAM_SCHEMA is defined as {**AGI_REASON_SCHEMA}
        assert set(AGI_STREAM_SCHEMA.keys()) >= set(AGI_REASON_SCHEMA.keys())

    def test_valid_reason_payload_valid_in_stream_schema(self):
        err = validate_fields(
            {"query": "explain this", "goals": ["clarity"], "include_reasoning_summary": False},
            AGI_STREAM_SCHEMA,
        )
        assert err is None

    def test_temperature_validation_inherited(self):
        err = validate_fields({"temperature": 3.0}, AGI_STREAM_SCHEMA)
        assert err is not None


# ---------------------------------------------------------------------------
# AGI_ANALYZE_SCHEMA
# ---------------------------------------------------------------------------


class TestAgiAnalyzeSchema:
    def test_inherits_base_schema(self):
        # AGI_ANALYZE_SCHEMA = {**AGI_BASE_SCHEMA}
        assert set(AGI_ANALYZE_SCHEMA.keys()) == set(AGI_BASE_SCHEMA.keys())

    def test_valid_payload(self):
        err = validate_fields({"query": "What does this do?", "verbose": True}, AGI_ANALYZE_SCHEMA)
        assert err is None

    def test_invalid_temperature_rejected(self):
        err = validate_fields({"temperature": -1}, AGI_ANALYZE_SCHEMA)
        assert err is not None


# ---------------------------------------------------------------------------
# SUBSCRIPTION_SCHEMA
# ---------------------------------------------------------------------------


class TestSubscriptionSchema:
    def test_user_id_required(self):
        err = validate_fields({}, SUBSCRIPTION_SCHEMA)
        assert err is not None
        assert "user_id" in err

    def test_user_id_present_valid(self):
        err = validate_fields({"user_id": "usr_123"}, SUBSCRIPTION_SCHEMA)
        assert err is None

    def test_user_id_empty_string_invalid(self):
        err = validate_fields({"user_id": ""}, SUBSCRIPTION_SCHEMA)
        assert err is not None
        assert "user_id" in err

    def test_tier_free_valid(self):
        err = validate_fields({"user_id": "u1", "tier": "FREE"}, SUBSCRIPTION_SCHEMA)
        assert err is None

    def test_tier_pro_valid(self):
        err = validate_fields({"user_id": "u1", "tier": "PRO"}, SUBSCRIPTION_SCHEMA)
        assert err is None

    def test_tier_enterprise_valid(self):
        err = validate_fields({"user_id": "u1", "tier": "ENTERPRISE"}, SUBSCRIPTION_SCHEMA)
        assert err is None

    def test_tier_invalid_rejected(self):
        err = validate_fields({"user_id": "u1", "tier": "PREMIUM"}, SUBSCRIPTION_SCHEMA)
        assert err is not None
        assert "tier" in err

    def test_tier_lowercase_rejected(self):
        err = validate_fields({"user_id": "u1", "tier": "free"}, SUBSCRIPTION_SCHEMA)
        assert err is not None

    def test_tier_absent_is_valid(self):
        err = validate_fields({"user_id": "u1"}, SUBSCRIPTION_SCHEMA)
        assert err is None
