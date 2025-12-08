Azure quota / premium allowance handling
=====================================

What this message means
-----------------------

If you see an error like "exceeded your premium request allowance" it means the Azure OpenAI resource you're using has reached a billing, quota, or premium allowance limit. This commonly happens when:

- The Azure OpenAI resource has a per-minute or per-day request quota configured.
- You're using a subscription or deployment tier that limits premium model usage.
- Billing or subscription issues prevent additional requests.

How Aria now behaves
---------------------

To improve robustness and reduce surprising failures, Aria now:

- Detects Azure quota/premium allowance errors (heuristically) across calls.
- For chat completions (Azure OpenAI provider) it returns a friendly message instead of raising an unexpected exception. Streaming responses will yield a single helpful message explaining the quota issue.
- For embeddings (used by memory/store), when Azure embeddings fail due to quota or premium errors we automatically fall back to a lightweight deterministic local hash embedding so features that rely on embeddings continue to function (with reduced semantic quality).
- For image generation endpoints we add friendlier error text for quota cases and still return a fallback image so the UI remains usable.

Files changed
-------------

- shared/azure_utils.py — new heuristics & helpers for detecting quota/rate-limit errors and producing a short actionable message.
- talk-to-ai/src/chat_providers.py — AzureOpenAIProvider now retries transient rate-limit errors and surfaces user-friendly quota messages instead of raising fatal exceptions.
- shared/chat_memory.py — embedding generation now falls back to local hashing when Azure embedding calls return quota / premium errors.
- function_app.py — image endpoint now formats nicer error text on quota conditions.

Next steps — When you see this message
------------------------------------

1. Check your Azure subscription and resource quotas in the Azure portal (open the Azure OpenAI resource -> Quotas + usage).
2. Review your choice of deployment and pricing tier. Premium-tier models and large deployments may have stricter quotas.
3. Consider spacing requests, reducing batch sizes, or switching to a different provider (OPENAI_API_KEY, LMStudio, or the local provider) when appropriate.
4. Enable monitoring and alerts for quota usage in Azure Monitor so you can proactively increase limits or throttle workloads.

Quick troubleshooting example
---------------------------

If you encounter the "premium request allowance" message during normal usage:

1. Confirm the resource used by the environment (AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT).
2. In the Azure portal check 'Usage + quotas' for that resource and raise a support request if necessary.
3. If you want to avoid relying on Azure for sensitive tasks, configure a fallback provider in the environment variables or CPI chain (OpenAI keys, LMStudio, or local LoRA).

Testing
-------

We include unit tests that exercise how Aria's HTTP image endpoint handles quota/premium errors. The tests live in `tests/test_function_app_image_quota.py` and use lightweight module stubs for `azure.functions` and the `openai` client so they can run in local developer environments and CI:

- Simulate an OpenAI / Azure image quota message (text matching heuristics) and assert the endpoint returns a helpful, user-facing message and a fallback image.
- Simulate an Azure-style exception (403 / nested error.code like `quota_exceeded`) and verify the friendly message is returned.
- Test the successful OpenAI image path (images.generate returning a URL) to ensure the endpoint still returns an `image_url` in normal operation.

If you need to re-run these tests locally they are fast and isolated; use `pytest tests/test_function_app_image_quota.py` from the repository root.
