# Research: Remove Exponential Backoff and Env-Var Retry Config

**Feature**: `004-remove-backoff` | **Date**: 2026-05-15

## Summary

No external research required. All decisions are determined by the existing codebase and the motivation documented in the spec.

---

## Decision 1: Fixed vs Exponential Delay

**Decision**: Replace exponential backoff with a fixed `retry_delay` seconds between attempts.

**Rationale**: The exponential schedule was introduced to work around aggressive rate-limiting from medium.com in CI. That problem is now solved at a higher level by the Freedium fallback (PR #7): 403/429 responses trigger an immediate switch to Freedium rather than retrying against medium.com at all. The exponential schedule therefore provides no additional resilience but adds complexity and unpredictability to retry timing.

**Alternatives considered**:
- Keep exponential, remove only env vars → Rejected. Removes the tooling noise but keeps the unnecessary complexity in the core retry loop.
- Keep exponential, add deprecation warning → Rejected. A deprecation period is unnecessary for an internal mechanism not part of the public API.

---

## Decision 2: Remove Fixtures vs Hardcode Defaults

**Decision**: Delete the `http_retries` and `http_retry_delay` pytest fixtures from `conftest.py` and inline `retries=3, retry_delay=2.0` directly in integration test calls.

**Rationale**: The fixtures existed as thin wrappers around env-var reads. Once the env vars are removed, the fixtures become single-line constants with no abstraction value. Inlining the defaults removes a layer of indirection that would otherwise require readers to trace through `conftest.py` to understand what values are used.

**Alternatives considered**:
- Keep fixtures with hardcoded defaults → Rejected. A fixture returning a literal integer is dead abstraction; it signals configurability that doesn't exist.
- Move constants to a `conftest.py` module-level variable → Rejected. Same problem — adds indirection without benefit.

---

## Decision 3: Handling `conftest.py` After Fixture Removal

**Decision**: Delete `conftest.py` entirely since removing both fixtures leaves the file empty (only `import os` and two functions, all of which are removed).

**Rationale**: An empty `conftest.py` is harmless but misleading — it implies there is shared test configuration when there is none. Deleting it is cleaner.

**Alternatives considered**:
- Leave empty file → Rejected. No benefit; creates noise in the file tree.
