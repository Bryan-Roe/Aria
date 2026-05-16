---
name: subscription-feature-gate-workflow
description: Add, debug, or audit subscription feature gates and usage limits in shared/subscription_manager.py. Use when a feature is incorrectly accessible to FREE users, quota limits are not enforcing, usage counters are wrong, or a new tier gate needs to be added to an endpoint.
argument-hint: "Describe the gap: wrong tier accessing a feature, quota not blocking, counter off, or new feature needs gating."
---

# Subscription Feature Gate Workflow

## What This Skill Produces
Correct, consistent feature-gate and usage-limit enforcement across all API endpoints — with proper 403 vs 429 responses, ENTERPRISE exemptions, and counter tracking aligned to the subscription tier model.

## When to Use

Trigger phrases:
- "FREE user accessing paid feature"
- "quota not enforcing"
- "usage counter wrong"
- "add subscription gate to endpoint"
- "ENTERPRISE limit not bypassed"
- "subscription tier check failing"
- "429 not returned when limit exceeded"
- "403 not returned for missing feature"
- "subscription data corrupted"
- "add new feature to PRO tier"
- "monthly usage reset not working"

## Tier Reference

| Tier | Price | Chat Msgs | Quantum Jobs | Training Hrs |
| ------ | ------- | ----------- | ------------- | ------------- |
| FREE | $0/mo | 100/mo | 0 | 0 |
| PRO | $49/mo | 10,000/mo | 50/mo | 20 hrs/mo |
| ENTERPRISE | $199/mo | Unlimited | Unlimited | Unlimited |

## Gatable Features (10 total)
`BASIC_CHAT`, `ARIA_CHARACTER`, `QUANTUM_COMPUTING`, `ADVANCED_TRAINING`, `WEBSITE_MAKER`, `API_ACCESS`, `CUSTOM_MODELS`, `PRIORITY_SUPPORT`, `ANALYTICS_DASHBOARD`, `BATCH_PROCESSING`

## Procedure

### Step 1 — Audit Existing Gate for the Endpoint
Search for the endpoint in `function_app.py` and check whether it calls both `has_feature()` and `check_limit()`:
```bash
grep -n "has_feature\|check_limit\|increment_usage" function_app.py
```
Both checks are required. Missing `check_limit` allows feature access without quota enforcement.

### Step 2 — Correct Gate Pattern
```python
from shared.subscription_manager import get_subscription_manager, Feature

mgr = get_subscription_manager()
sub = mgr.get_subscription(user_id)

# 1. Feature gate FIRST (returns 403)
if not sub.has_feature(Feature.QUANTUM_COMPUTING):
    return func.HttpResponse("Upgrade to PRO for quantum access", status_code=403)

# 2. Usage limit SECOND (returns 429)
if not sub.check_limit('quantum_jobs'):
    return func.HttpResponse("Monthly quantum job quota exceeded", status_code=429)

# 3. Track usage AFTER confirming capacity
sub.increment_usage('quantum_jobs')
```

**Critical order**: `has_feature()` → `check_limit()` → work → `increment_usage()`.
Never increment usage before confirming the limit check passes.

### Step 3 — ENTERPRISE Exemption
ENTERPRISE tier has no limits — `check_limit()` always returns `True` for ENTERPRISE. Never add special-case ENTERPRISE bypass code; the tier model handles it automatically. Verify:
```python
sub = mgr.get_subscription("enterprise-user-id")
print(sub.tier)  # → "ENTERPRISE"
print(sub.check_limit('quantum_jobs'))  # → True (unlimited)
```

### Step 4 — Verify Response Codes
- 403 → user lacks the feature (wrong tier, needs upgrade)
- 429 → user has the feature but exceeded their monthly quota

Do not swap these — clients and monitoring tools distinguish them for billing and UX flows.

### Step 5 — Inspect Subscription Data File
```bash
cat data_out/subscriptions/subscriptions.json | python -m json.tool
```
Subscription data lives in `data_out/subscriptions/subscriptions.json` — never in `datasets/`.
Check fields: `tier`, `usage_counts`, `active`, `reset_date`.

### Step 6 — Monthly Reset
```python
sub.reset_usage()  # Resets all counters; called monthly
sub.is_active()    # Returns False if subscription expired
```
If counters are stuck after month rollover, call `reset_usage()` manually or restart the host to trigger reload.

### Step 7 — Adding a New Feature Gate
1. Add the feature to the `Feature` enum in `subscription_manager.py`
2. Update `TIER_FEATURES` dict: assign feature to correct tier(s)
3. Update `TIER_LIMITS` if the feature has a numeric quota
4. Add `has_feature()` + `check_limit()` guards to all relevant endpoints
5. Update tier documentation if pricing changes
6. Run unit tests: `python scripts/test_runner.py --unit`

**Never modify tier definitions without updating all endpoint gates.**

## Quality Checks
- [ ] `has_feature()` called before `check_limit()` — feature gate always comes first
- [ ] 403 returned for missing features, 429 for exceeded limits (not swapped)
- [ ] `increment_usage()` called only after both checks pass
- [ ] ENTERPRISE tier skips quota tracking (no special-case code needed)
- [ ] Subscription data stored in `data_out/subscriptions/` (not `datasets/`)
- [ ] New features added to both `TIER_FEATURES` and relevant endpoint guards
- [ ] Unit tests pass after gate changes: `python scripts/test_runner.py --unit`
