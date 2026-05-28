"""Email spam classification workflow definition.

Flow:
  user email -> classifier -> (spam confirmation | raw email display)

The classifier must emit exactly `SPAM` or `NOT_SPAM`. Conditional edges use
the workflow builder's `condition=` argument to route into the appropriate
follow-up node.
"""

from __future__ import annotations

import os
from typing import Any, Callable

from agent_framework import WorkflowBuilder
from agent_framework.azure import AzureAIClient
from azure.identity.aio import DefaultAzureCredential


CLASSIFIER_INSTRUCTIONS = """\
You are an email spam classifier.

Inspect the raw email content for spam indicators such as:
- promotional or urgency-heavy language
- suspicious or mismatched links
- requests for credentials, payments, or account verification
- lottery, giveaway, or prize claims
- obvious phishing or spoofing patterns

Output rules:
- Reply with exactly SPAM if the email is spam or likely spam.
- Reply with exactly NOT_SPAM if the email appears legitimate.
- Output only one token: SPAM or NOT_SPAM.
"""

SPAM_CONFIRMATION_INSTRUCTIONS = """\
You receive a conversation where the classifier has already decided the email is spam.

Reply with exactly this sentence and nothing else:
This email was classified as SPAM.
"""

RAW_EMAIL_DISPLAY_INSTRUCTIONS = """\
You receive the original user email plus prior workflow context.

Find the raw email content from the user's original message and output that raw
email text verbatim. Do not summarize it. Do not add labels, quotes, markdown,
or explanation. Output only the original email content.
"""


def _get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    raise ValueError(
        f"{name} is not set. Add it to your .env file or environment variables."
    )


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    text = getattr(value, "text", None)
    if isinstance(text, str):
        return text

    content = getattr(value, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(part for part in content if isinstance(part, str))

    data = getattr(value, "data", None)
    if data is not None and data is not value:
        coerced = _coerce_text(data)
        if coerced:
            return coerced

    output = getattr(value, "output", None)
    if output is not None and output is not value:
        coerced = _coerce_text(output)
        if coerced:
            return coerced

    choices = getattr(value, "choices", None)
    if isinstance(choices, list):
        joined = " ".join(_coerce_text(choice) for choice in choices)
        if joined:
            return joined

    return str(value)


def _make_label_condition(expected_label: str) -> Callable[..., bool]:
    normalized_expected = expected_label.strip().upper()

    def _condition(*args: Any, **kwargs: Any) -> bool:
        values = [*args, *kwargs.values()]
        for value in values:
            normalized = _coerce_text(value).strip().upper()
            if normalized == normalized_expected:
                return True
        return False

    return _condition


def build_workflow():
    """Construct the three-node email spam workflow."""
    endpoint = _get_required_env("AZURE_AI_PROJECT_ENDPOINT")
    model = _get_required_env("FOUNDRY_MODEL_DEPLOYMENT_NAME")

    credential = DefaultAzureCredential()

    classifier = AzureAIClient(
        project_endpoint=endpoint,
        credential=credential,
    ).as_agent(
        name="SpamClassifier",
        model=model,
        instructions=CLASSIFIER_INSTRUCTIONS,
    )

    spam_confirmation = AzureAIClient(
        project_endpoint=endpoint,
        credential=credential,
    ).as_agent(
        name="SpamConfirmation",
        model=model,
        instructions=SPAM_CONFIRMATION_INSTRUCTIONS,
    )

    raw_email_display = AzureAIClient(
        project_endpoint=endpoint,
        credential=credential,
    ).as_agent(
        name="RawEmailDisplay",
        model=model,
        instructions=RAW_EMAIL_DISPLAY_INSTRUCTIONS,
    )

    return (
        WorkflowBuilder(start_executor=classifier)
        .add_edge(classifier, spam_confirmation, condition=_make_label_condition("SPAM"))
        .add_edge(classifier, raw_email_display, condition=_make_label_condition("NOT_SPAM"))
        .build()
    )