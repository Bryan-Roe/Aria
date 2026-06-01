"""Lightweight extractive summarization helpers for local/offline fallbacks."""

from __future__ import annotations

import re
from collections import Counter

_SUMMARY_HINTS = (
    "summarize",
    "summary",
    "summarise",
    "tl;dr",
    "tldr",
    "gist",
    "recap",
)

_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'-]*")
_WHITESPACE_RE = re.compile(r"\s+")
_INLINE_PREFIX_RE = re.compile(
    r"^\s*(?:please\s+)?(?:can you\s+|could you\s+)?"
    r"(?:summari[sz]e|give me|write)\s+"
    r"(?:a\s+)?(?:short\s+|brief\s+|quick\s+)?"
    r"(?:summary|recap|gist|tl;dr|tldr|this|the following|the text|this text)?"
    r"\s*[:\-]\s*",
    re.IGNORECASE,
)

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "hers",
    "him",
    "his",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "ours",
    "she",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "they",
    "this",
    "those",
    "to",
    "us",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "will",
    "with",
    "you",
    "your",
    "yours",
}


def normalize_text(text: str) -> str:
    """Collapse whitespace for more stable sentence scoring."""
    return _WHITESPACE_RE.sub(" ", (text or "").strip())


def is_summary_request(text: str) -> bool:
    """Return True when the prompt looks like a summarization request."""
    lowered = normalize_text(text).lower()
    return any(hint in lowered for hint in _SUMMARY_HINTS)


def _split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    return [piece.strip(" -\t") for piece in pieces if piece and piece.strip()]


def _strip_summary_prompt(text: str) -> str:
    normalized = normalize_text(text)
    stripped = _INLINE_PREFIX_RE.sub("", normalized)
    return stripped or normalized


def _looks_like_instruction(sentence: str) -> bool:
    lowered = sentence.strip().lower()
    tokens = _WORD_RE.findall(lowered)
    return len(tokens) <= 12 and any(hint in lowered for hint in _SUMMARY_HINTS)


def _sentence_tokens(sentence: str) -> list[str]:
    return [
        token.lower() for token in _WORD_RE.findall(sentence) if len(token) > 2 and token.lower() not in _STOP_WORDS
    ]


def summarize_text(text: str, *, max_sentences: int = 3, max_chars: int = 420) -> str:
    """Create a deterministic extractive summary without external dependencies."""
    cleaned = _strip_summary_prompt(text)
    if not cleaned:
        return ""

    sentences = _split_sentences(cleaned)
    while len(sentences) > 1 and _looks_like_instruction(sentences[0]):
        sentences = sentences[1:]

    if not sentences:
        return cleaned[:max_chars].rstrip()

    if len(sentences) == 1:
        return sentences[0][:max_chars].rstrip()

    tokenized_sentences = [_sentence_tokens(sentence) for sentence in sentences]
    frequencies: Counter[str] = Counter()
    for tokens in tokenized_sentences:
        frequencies.update(tokens)

    if not frequencies:
        ordered = sentences[: min(2, len(sentences))]
    else:
        max_frequency = max(frequencies.values())
        weights = {token: count / max_frequency for token, count in frequencies.items()}
        scored: list[tuple[float, int, str]] = []
        for idx, (sentence, tokens) in enumerate(zip(sentences, tokenized_sentences)):
            if not tokens:
                score = 0.02
            else:
                density = sum(weights[token] for token in set(tokens)) / len(tokens)
                lead_bonus = 0.12 if idx == 0 else 0.06 if idx == 1 else 0.0
                detail_bonus = 0.08 if any(ch.isdigit() for ch in sentence) else 0.0
                score = density + lead_bonus + detail_bonus
            scored.append((score, idx, sentence))

        target_count = min(max_sentences, 2 if len(sentences) <= 4 else 3)
        top_sentences = sorted(
            sorted(scored, key=lambda item: item[0], reverse=True)[:target_count],
            key=lambda item: item[1],
        )
        ordered = [sentence for _, _, sentence in top_sentences]

    selected: list[str] = []
    total_chars = 0
    for sentence in ordered:
        candidate = sentence if sentence.endswith((".", "!", "?")) else f"{sentence}."
        projected = total_chars + len(candidate) + (1 if selected else 0)
        if projected > max_chars and selected:
            break
        if not selected and len(candidate) > max_chars:
            return candidate[: max_chars - 3].rstrip() + "..."
        selected.append(candidate)
        total_chars = projected

    return " ".join(selected) if selected else sentences[0][:max_chars].rstrip()
