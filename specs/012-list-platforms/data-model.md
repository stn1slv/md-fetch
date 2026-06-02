# Phase 1 Data Model: List Supported Platforms

This feature introduces no persistent storage and no new runtime objects beyond a
read-only projection of the existing provider registry.

## Entity: Supported Platform

A projection of one entry in the router registry (`_REGISTRY`).

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `domain` | `str` | `_REGISTRY` key | Registered domain (e.g. `medium.com`, `dev.to`). |
| `matches_subdomains` | `bool` | provider class `MATCH_SUBDOMAINS` | Whether subdomains of `domain` also route to this provider (multi-tenant platforms). |

### Accessor contract

```python
def supported_platforms() -> list[tuple[str, bool]]:
    """Return (domain, matches_subdomains) for every registered provider,
    sorted ascending by domain."""
```

- **Ordering**: ascending by `domain` (deterministic — FR-005).
- **Completeness**: exactly one tuple per registered domain — no missing, no extra
  (SC-002). Derived live from the registry, so new providers appear automatically
  (FR-002, SC-003).
- **Purity**: read-only; no mutation of `_REGISTRY`; no side effects; no network.

### Relationship to existing `supported_domains()`

`supported_domains() -> frozenset[str]` is retained unchanged (still used by the
unsupported-platform error message). `supported_platforms()` is the
subdomain-aware superset used by the list operation. No behavior change to
existing callers.

### Validation rules

- A platform with `matches_subdomains == True` is rendered with a `*.<domain>`
  wildcard annotation; `False` renders the bare domain (FR-006).
- No two tuples share the same `domain` (registry keys are unique by construction).
