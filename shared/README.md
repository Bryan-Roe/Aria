# Shared Infrastructure — Tier System

The `shared/` directory is organized by import dependency tier to make it clear what's required at runtime and what's optional.

## Tier Levels (bottom-up)

### 🔵 Core Tier (`shared/core/`)

**Always required.** Minimal dependencies, no AI project imports.

- **module_registry.py** — Central import hub for all ai-projects; replaces all sys.path manipulation
- Other: script utilities, config validation, helpers

**Import into other tiers without restriction.**

```python
from shared.core.module_registry import AIProjectsRegistry

# Instead of:
# from chat_providers import detect_provider
# from token_utils import prune_messages

# Use:
registry = AIProjectsRegistry()
chat_api = registry.chat_cli()
detect_provider = chat_api.detect_provider
```

---

### 🟢 Infrastructure Tier (`shared/infrastructure/`)

**Heavy dependencies**: SQL engines, Cosmos DB, telemetry, observability.

- `sql_engine.py` — SQL connection pool management
- `cosmos_client.py` — Azure Cosmos DB integration
- `telemetry.py` — Application Insights tracing
- `db_logging.py` — Fault-tolerant DB logging

**Must be imported with try/except and feature-flagged in production.**

```python
# In function_app.py:
try:
    from shared.infrastructure.sql_engine import sql_health
    db_available = True
except ImportError:
    db_available = False
```

**Can depend on**: Core tier

---

### 🟡 Domain Tier (`shared/domain/`)

**AI-specific utilities**: Chat providers, memory systems, token management.

- `chat_providers.py` — Chat provider detection, streaming, fallback
- `chat_memory.py` — Semantic memory and embeddings
- `token_utils.py` — Token counting and context pruning
- `agi_provider.py` — AGI reasoning chain provider
- `config_validator.py` — YAML schema validation

**Used by**: AI endpoints (`/api/chat`), orchestrators, training scripts

**Can depend on**: Core, Infrastructure tiers

---

### 🟠 Utilities Tier (`shared/utilities/`)

**Lightweight helpers** with no heavy dependencies.

- `file_cache.py` — In-memory and disk caching
- `http_utils.py` — HTTP client helpers
- `json_utils.py` — JSON serialization utilities
- `performance_utils.py` — Timing and profiling
- `request_validator.py` — Request schema validation

**Can depend on**: Core, Utilities, Domain (limited)

---

### 🔴 Premium Tier (`shared/premium/`)

**Feature-gated monetization and advanced features.**

- `subscription_manager.py` — Tier-based access control (FREE/PRO/ENTERPRISE)
- `referral_system.py` — Referral tracking and rewards
- `stripe_webhooks.py` — Stripe payment webhooks
- `email_notifications.py` — Email alerts and notifications

**Must be imported with try/except; graceful fallback if missing.**

```python
# In function_app.py or endpoints:
try:
    from shared.premium.subscription_manager import check_subscription
    feature_available = check_subscription(user_id, 'quantum_jobs')
except ImportError:
    feature_available = False
```

**Can depend on**: Core, Utilities, Domain (limited)

---

## Dependency Graph (what can import what)

```text
Core
  ↑
  │ depends on
  │
Infrastructure, Domain, Utilities, Premium
  ↑
  │
Applications (function_app.py, scripts/, apps/)
```

**Rule**: Never import upward in the dependency graph.

- ✗ Core cannot import from Domain or Infrastructure
- ✓ Domain can import from Core
- ✓ function_app.py can import from all tiers

---

## Why This Structure?

1. **Clarity at deployment time** — Know exactly what's required vs optional
2. **Easier to deprecate** — Move old modules to `shared/deprecated/` without breaking core
3. **Safe feature gating** — Premium features don't crash if not available
4. **Testing** — Mock entire tiers without affecting Core
5. **Microservice extraction** — Move Infrastructure tier to separate service later

---

## Conventions

### Import Paths by Tier

```python
# ✓ Core imports
from shared.core.module_registry import AIProjectsRegistry

# ✓ Infrastructure imports (with try/except where applicable)
from shared.infrastructure.sql_engine import sql_health
from shared.infrastructure.telemetry import get_tracer

# ✓ Domain imports
from shared.domain.chat_providers import detect_provider
from shared.domain.token_utils import prune_messages
from shared.domain.chat_memory import retrieve_similar

# ✓ Utilities imports
from shared.utilities.file_cache import FileCache
from shared.utilities.performance_utils import timer

# ✓ Premium imports (always with try/except)
try:
    from shared.premium.subscription_manager import get_subscription_tier
except ImportError:
    get_subscription_tier = lambda uid: "FREE"
```

### Module Initialization

Each tier should have a clear `__init__.py` that exports public APIs:

```python
# shared/domain/__init__.py
from .chat_providers import detect_provider, BaseChatProvider

__all__ = ['detect_provider', 'BaseChatProvider']
```

---

## Migration Guide

### If you see old-style imports

```python
# ❌ Old: root-level shims (deprecated)
from chat_providers import detect_provider
from token_utils import prune_messages

# ✓ New: use registry
from shared.core.module_registry import AIProjectsRegistry
registry = AIProjectsRegistry()
chat_api = registry.chat_cli()
detect_provider = chat_api.detect_provider
prune_messages = chat_api.token_utils.prune_messages
```

### If you see sys.path manipulation

```python
# ❌ Old: scattered sys.path
sys.path.insert(0, 'ai-projects/chat-cli/src')
sys.path.insert(0, 'ai-projects/quantum-ml/src')

# ✓ New: centralized registration
from shared.core.module_registry import AIProjectsRegistry
AIProjectsRegistry.register_paths(['chat-cli', 'quantum-ml'])
```

---

## Next Steps

1. **Move modules to tiers gradually** — Start with Infrastructure, Domain, Utilities
2. **Update imports in function_app.py** — Use AIProjectsRegistry for ai-projects
3. **Create ai.py files in each ai-project** — Define public API contracts
4. **Add safe fallback imports** — Wrap Infrastructure and Premium imports with try/except
5. **Update .github/instructions/** — Document new import patterns for future AI agents
