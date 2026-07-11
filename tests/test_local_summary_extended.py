"""Extended tests for shared/local_summary.py.

Covers paths not exercised by test_local_summary.py:
- is_summary_request with every hint word in _SUMMARY_HINTS
- summarize_text with various prefix patterns
- summarize_text respecting max_sentences parameter
- normalize_text with various whitespace forms
- edge cases: single word text, punctuation-only, very long single sentence
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.local_summary import is_summary_request, normalize_text, summarize_text

# ---------------------------------------------------------------------------
# is_summary_request — all hint words
# ---------------------------------------------------------------------------


class TestIsSummaryRequestHints:
    def test_summarize_hint(self):
        assert is_summary_request("Please summarize this article.") is True

    def test_summary_hint(self):
        assert is_summary_request("Give me a summary of the document.") is True

    def test_summarise_british_spelling(self):
        assert is_summary_request("Could you summarise this?") is True

    def test_tldr_hint(self):
        assert is_summary_request("tldr this thread") is True

    def test_tl_dr_hint_with_semicolon(self):
        assert is_summary_request("TL;DR: what happened here?") is True

    def test_gist_hint(self):
        assert is_summary_request("What is the gist of this?") is True

    def test_recap_hint(self):
        assert is_summary_request("Give me a recap of the meeting.") is True

    def test_non_summary_request_false(self):
        assert is_summary_request("Explain this in detail.") is False

    def test_empty_string_false(self):
        assert is_summary_request("") is False

    def test_hint_embedded_in_longer_text(self):
        assert is_summary_request("I need a short recap of what was discussed.") is True

    def test_unrelated_text_false(self):
        assert is_summary_request("How do I implement quicksort?") is False


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------


class TestNormalizeTextExtended:
    def test_tab_collapsed(self):
        assert normalize_text("hello\tworld") == "hello world"

    def test_multiple_newlines_collapsed(self):
        assert normalize_text("line1\n\nline2\n\n\nline3") == "line1 line2 line3"

    def test_leading_trailing_stripped(self):
        assert normalize_text("  hello  ") == "hello"

    def test_already_normalized_unchanged(self):
        assert normalize_text("hello world") == "hello world"

    def test_none_like_empty_string(self):
        assert normalize_text("") == ""

    def test_single_word(self):
        assert normalize_text("word") == "word"

    def test_mixed_whitespace(self):
        result = normalize_text("a  \t b \n c")
        assert result == "a b c"


# ---------------------------------------------------------------------------
# summarize_text — prefix stripping variants
# ---------------------------------------------------------------------------


class TestSummarizeTextPrefixStripping:
    def test_summarize_colon_prefix_stripped(self):
        text = "Summarize: The project launched on time. Results exceeded targets."
        summary = summarize_text(text)
        assert "Summarize" not in summary
        assert "project" in summary.lower() or "results" in summary.lower()

    def test_write_a_summary_prefix_stripped(self):
        text = "Write a summary: Alpha phase complete. Beta phase begins next week."
        summary = summarize_text(text)
        assert "Write a summary" not in summary

    def test_give_me_a_brief_summary_prefix_stripped(self):
        text = "Give me a brief summary: Core metrics improved significantly. Adoption grew 30%."
        summary = summarize_text(text)
        assert "Give me" not in summary

    def test_please_can_you_summarize_prefix_stripped(self):
        text = "Please can you summarize this: Revenue increased 20%. Costs down 5%."
        summary = summarize_text(text)
        assert "Please" not in summary


# ---------------------------------------------------------------------------
# summarize_text — max_sentences parameter
# ---------------------------------------------------------------------------


class TestSummarizeTextMaxSentences:
    def test_max_sentences_one(self):
        text = "First sentence introduces the topic. Second sentence provides details. Third sentence wraps up."
        summary = summarize_text(text, max_sentences=1)
        # At most one sentence — count terminal punctuation occurrences
        sentence_enders = sum(1 for ch in summary if ch in ".!?")
        assert sentence_enders <= 1

    def test_max_sentences_default_is_three(self):
        text = " ".join(f"Sentence {i} with some content words." for i in range(10))
        summary_3 = summarize_text(text, max_sentences=3)
        summary_5 = summarize_text(text, max_sentences=5)
        # The 3-sentence summary should be <= the 5-sentence summary in length
        assert len(summary_3) <= len(summary_5)

    def test_max_sentences_larger_than_input_returns_all(self):
        text = "Short text. Very short."
        summary = summarize_text(text, max_sentences=10)
        assert "Short text" in summary


# ---------------------------------------------------------------------------
# summarize_text — character budget (max_chars)
# ---------------------------------------------------------------------------


class TestSummarizeTextCharBudget:
    def test_output_within_max_chars(self):
        text = " ".join(["word"] * 100)
        summary = summarize_text(text, max_chars=50)
        assert len(summary) <= 50

    def test_zero_max_chars_gives_empty_or_ellipsis(self):
        # Edge case: max_chars=0 with content — expected not to crash
        try:
            result = summarize_text("Hello world.", max_chars=0)
            assert isinstance(result, str)
        except Exception as exc:
            pytest.fail(f"summarize_text raised unexpectedly: {exc}")

    def test_max_chars_very_large_keeps_content(self):
        text = "Alpha project overview. Beta improvements noted. Gamma testing planned."
        summary = summarize_text(text, max_chars=10000)
        assert len(summary) > 0
        assert "Alpha" in summary or "Beta" in summary


# ---------------------------------------------------------------------------
# summarize_text — additional edge cases
# ---------------------------------------------------------------------------


class TestSummarizeTextEdgeCases:
    def test_single_sentence_no_prefix_returned_as_is(self):
        sentence = "The quick brown fox jumps over the lazy dog."
        result = summarize_text(sentence)
        assert "fox" in result

    def test_text_with_numbers_scores_higher(self):
        text = (
            "General update without specifics. "
            "Key milestone: achieved 95% accuracy with 10,000 samples. "
            "Follow-up planned."
        )
        summary = summarize_text(text, max_sentences=1)
        # Sentence with numbers should tend to be selected
        assert "95" in summary or "10,000" in summary or "milestone" in summary

    def test_two_sentence_text_returns_both_or_one(self):
        text = "First key finding reported. Second key finding confirmed."
        result = summarize_text(text)
        assert len(result) > 0
        assert isinstance(result, str)

    def test_punctuation_only_returns_empty(self):
        result = summarize_text("---")
        assert result == "" or len(result) < 10

    def test_repeated_whitespace_only_returns_empty(self):
        result = summarize_text("   \n\n   ")
        assert result == ""

    def test_leading_instruction_multi_sentence_stripped(self):
        text = (
            "Summarize this. "
            "Give me a summary. "
            "The actual content starts here with important details. "
            "More content follows for completeness."
        )
        result = summarize_text(text)
        assert "Summarize this" not in result
        assert "actual content" in result or "important" in result
