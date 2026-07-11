"""Tests for shared/logging.py.

Covers JsonFormatter output, configure_logging idempotency,
configure_json_logging alias, and get_logger behaviour.
"""

from __future__ import annotations

import io
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Reset module-level _configured flag before importing so tests are isolated.
import shared.logging as shared_logging_mod
from shared.logging import (
    JsonFormatter,
    configure_json_logging,
    configure_logging,
    get_logger,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_record(
    name: str = "test.logger",
    level: int = logging.INFO,
    msg: str = "hello",
    exc_info: bool = False,
    **extra,
) -> logging.LogRecord:
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname="/some/path.py",
        lineno=42,
        msg=msg,
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def _parse_formatted(formatter: JsonFormatter, record: logging.LogRecord) -> dict:
    return json.loads(formatter.format(record))


# ---------------------------------------------------------------------------
# JsonFormatter — basic fields
# ---------------------------------------------------------------------------


class TestJsonFormatterBasicFields:
    def test_output_is_valid_json(self):
        f = JsonFormatter()
        record = _make_record()
        output = f.format(record)
        assert json.loads(output)  # does not raise

    def test_level_field_present(self):
        f = JsonFormatter()
        doc = _parse_formatted(f, _make_record(level=logging.WARNING))
        assert doc["level"] == "WARNING"

    def test_logger_field_is_record_name(self):
        f = JsonFormatter()
        doc = _parse_formatted(f, _make_record(name="my.module"))
        assert doc["logger"] == "my.module"

    def test_message_field_matches_msg(self):
        f = JsonFormatter()
        doc = _parse_formatted(f, _make_record(msg="test message"))
        assert doc["message"] == "test message"

    def test_timestamp_field_present_and_z_suffix(self):
        f = JsonFormatter()
        doc = _parse_formatted(f, _make_record())
        assert "timestamp" in doc
        assert doc["timestamp"].endswith("Z")

    def test_no_exception_key_without_exc_info(self):
        f = JsonFormatter()
        doc = _parse_formatted(f, _make_record())
        assert "exception" not in doc


class TestJsonFormatterDebugLocation:
    def test_debug_record_has_location_field(self):
        f = JsonFormatter()
        record = _make_record(level=logging.DEBUG)
        doc = _parse_formatted(f, record)
        assert "location" in doc

    def test_info_record_has_no_location_field(self):
        f = JsonFormatter()
        record = _make_record(level=logging.INFO)
        doc = _parse_formatted(f, record)
        assert "location" not in doc

    def test_error_record_has_no_location_field(self):
        f = JsonFormatter()
        record = _make_record(level=logging.ERROR)
        doc = _parse_formatted(f, record)
        assert "location" not in doc


class TestJsonFormatterExtraFields:
    def test_extra_field_included_in_output(self):
        f = JsonFormatter()
        doc = _parse_formatted(f, _make_record(request_id="abc-123"))
        assert doc["request_id"] == "abc-123"

    def test_builtin_keys_not_duplicated_in_output(self):
        f = JsonFormatter()
        doc = _parse_formatted(f, _make_record())
        # These are built-in attributes that should not appear as extras
        assert "args" not in doc
        assert "funcName" not in doc
        assert "levelno" not in doc

    def test_multiple_extra_fields(self):
        f = JsonFormatter()
        doc = _parse_formatted(f, _make_record(user_id="u1", trace="t2"))
        assert doc["user_id"] == "u1"
        assert doc["trace"] == "t2"


class TestJsonFormatterExceptionHandling:
    def test_exception_field_set_when_exc_info_present(self):
        f = JsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/p.py",
            lineno=1,
            msg="error occurred",
            args=(),
            exc_info=exc_info,
        )
        doc = _parse_formatted(f, record)
        assert "exception" in doc
        assert "ValueError" in doc["exception"]


# ---------------------------------------------------------------------------
# configure_logging
# ---------------------------------------------------------------------------


class TestConfigureLogging:
    def setup_method(self):
        # Reset the module-level _configured flag between tests
        shared_logging_mod._configured = False
        root = logging.getLogger()
        # Remove all handlers to start clean
        for h in list(root.handlers):
            root.removeHandler(h)

    def test_adds_handler_on_first_call(self):
        buf = io.StringIO()
        configure_logging(level="INFO", stream=buf)
        root = logging.getLogger()
        assert len(root.handlers) >= 1

    def test_second_call_does_not_add_duplicate_handler(self):
        buf = io.StringIO()
        configure_logging(level="INFO", stream=buf)
        count_after_first = len(logging.getLogger().handlers)
        configure_logging(level="DEBUG", stream=buf)
        count_after_second = len(logging.getLogger().handlers)
        assert count_after_second == count_after_first

    def test_level_is_applied(self):
        buf = io.StringIO()
        configure_logging(level="WARNING", stream=buf)
        assert logging.getLogger().level == logging.WARNING

    def test_structured_true_uses_json_formatter(self):
        buf = io.StringIO()
        configure_logging(level="INFO", structured=True, stream=buf)
        root = logging.getLogger()
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
        assert any(isinstance(h.formatter, JsonFormatter) for h in stream_handlers)

    def test_structured_false_uses_plain_formatter(self):
        buf = io.StringIO()
        configure_logging(level="INFO", structured=False, stream=buf)
        root = logging.getLogger()
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
        plain = [h for h in stream_handlers if not isinstance(h.formatter, JsonFormatter)]
        assert len(plain) >= 1


class TestConfigureJsonLogging:
    def setup_method(self):
        shared_logging_mod._configured = False
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

    def test_configure_json_logging_uses_json_formatter(self):
        buf = io.StringIO()
        configure_json_logging(level="INFO", stream=buf)
        root = logging.getLogger()
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
        assert any(isinstance(h.formatter, JsonFormatter) for h in stream_handlers)


# ---------------------------------------------------------------------------
# get_logger
# ---------------------------------------------------------------------------


class TestGetLogger:
    def test_returns_logger_instance(self):
        log = get_logger("my.test.module")
        assert isinstance(log, logging.Logger)

    def test_logger_name_matches(self):
        log = get_logger("some.unique.name")
        assert log.name == "some.unique.name"

    def test_does_not_raise_when_root_has_no_handlers(self):
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)
        shared_logging_mod._configured = False
        # Should auto-configure instead of raising
        log = get_logger("auto.config.test")
        assert isinstance(log, logging.Logger)
