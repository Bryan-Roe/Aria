---
applyTo: "**/subscription_manager.py"
---

# Subscription Manager — Instruction Guide

## Tier Definitions

| Tier | Price | Chat Msgs | Quantum Jobs | Training Hrs |
| ------ | ------- | ----------- | ------------- | ------------- |
| FREE | $0/mo | 100/mo | 0 | 0 |
| PRO | $49/mo | 10,000/mo | 50/mo | 20 hrs/mo |
| ENTERPRISE | $199/mo | Unlimited | Unlimited | Unlimited |

## Feature Gating

```python
# 10 gatable features:
BASIC_CHAT, ARIA_CHARACTER, QUANTUM_COMPUTING, ADVANCED_TRAINING,
WEBSITE_MAKER, API_ACCESS, CUSTOM_MODELS, PRIORITY_SUPPORT,
ANALYTICS_DASHBOARD, BATCH_PROCESSING
```

## Usage Pattern

```python
from shared.subscription_manager import get_subscription_manager, Feature

mgr = get_subscription_manager()
sub = mgr.get_subscription(user_id)

# Feature check
if not sub.has_feature(Feature.QUANTUM_COMPUTING):
    return HttpResponse("Upgrade to PRO for quantum access", status_code=403)

# Usage limit check
if not sub.check_limit('quantum_jobs'):
    return HttpResponse("Monthly quota exceeded", status_code=429)

# Track usage
sub.increment_usage('quantum_jobs')

# Usage reporting
pct = sub.get_usage_percentage('chat_messages')  # → 0.0 to 1.0
```

## Subscription Lifecycle

```python
sub.is_active()         # Check if subscription is current
sub.reset_usage()       # Called monthly to reset counters
```

## Storage

- File: `data_out/subscriptions/subscriptions.json`
- Loaded on startup by `SubscriptionManager._load_subscriptions()`
- Persisted on changes

## Coding Conventions

- Always check `has_feature()` before `check_limit()` — feature gates come first
- Return 403 for missing features, 429 for exceeded limits
- ENTERPRISE tier has no limits — skip tracking for unlimited resources
- Never modify tier definitions without updating all endpoint gates
- Subscription data lives in `data_out/` (not `datasets/`)
