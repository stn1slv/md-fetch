# Phase 0 Research: List Supported Platforms

## R1 — How to expose the operation without breaking `md-fetch <URL>`

**Decision**: Make the `url` Click argument `required=False` and add a `--list-platforms`
boolean flag (`is_flag=True`, `is_eager=True`). When the flag is present, print the
list and `return` (exit 0) before any URL handling. When the flag is absent and
`url` is `None`, emit a usage error to stderr and exit with code 2 (Click's
conventional usage-error code), mirroring what Click does today for a missing
required argument.

**Rationale**: Click does not natively support "required unless another flag is
set", so the requiredness is enforced manually. `is_eager` ensures the flag is
parsed regardless of argument position. This preserves the existing
`md-fetch <URL>` contract (FR-001a) with the smallest possible change.

**Alternatives considered**:
- *Click sub-commands (`md-fetch list` / `md-fetch fetch <URL>`)* — rejected in the
  2026-06-02 clarification; breaks the bare `md-fetch <URL>` invocation.
- *Custom Click `Command.parse_args` override* — over-engineered for a single flag.

## R2 — Where the platform data comes from (subdomain awareness)

**Decision**: Add a thin accessor to `router.py` that returns each registered
domain paired with whether its provider matches subdomains, sorted by domain:
`supported_platforms() -> list[tuple[str, bool]]`. The CLI formats the output;
the router supplies the data (separation of concerns).

**Rationale**: The existing `supported_domains()` returns only a `frozenset[str]`
and loses the `MATCH_SUBDOMAINS` distinction required by FR-006. The registry
(`_REGISTRY: dict[str, type[BaseExtractor]]`) already holds the provider class,
whose `MATCH_SUBDOMAINS` class attribute carries the needed flag. A dedicated
accessor keeps the registry private and gives the CLI a stable, typed contract.

**Alternatives considered**:
- *Expose `_REGISTRY` directly* — leaks an internal mutable mapping; rejected.
- *Reuse `supported_domains()` and re-derive subdomain info in the CLI* — would
  force the CLI to import provider classes and read `MATCH_SUBDOMAINS`, duplicating
  routing knowledge in the presentation layer; rejected.

## R3 — Output rendering

**Decision**: Plain text to stdout, one platform per line, alphabetically sorted,
under a `Supported platforms:` header. Subdomain-matching platforms are rendered
as `<domain> (and *.<domain>)`; exact-match platforms are rendered as the bare
`<domain>`. Exit code 0.

Example:

```
Supported platforms:
  boomi.com
  dev.to
  dzone.com
  konghq.com
  medium.com (and *.medium.com)
  substack.com (and *.substack.com)
  thenewstack.io
```

**Rationale**: Human-readable for terminal use (FR-003, SC-001); the `(and *.x)`
suffix satisfies FR-006/SC-004 without inventing structured metadata (out of scope
per Assumptions). Alphabetical order satisfies FR-005/determinism.

**Alternatives considered**:
- *JSON / `--format` option* — explicitly out of scope for v1.
- *Two separate lines (`medium.com` + `*.medium.com`)* — noisier; a single
  annotated line reads better and still distinguishes the two cases.

## R4 — Testing approach

**Decision**: Unit tests only (`tests/unit/test_cli.py`), using `CliRunner`. Assert:
(1) `--list-platforms` exits 0 and output contains every supported domain;
(2) a subdomain platform shows the `*.` wildcard and an exact-match one does not;
(3) no `extract` call is made (network) — patch `mdfetch.cli.extract` and assert
not called; (4) invoking with neither URL nor flag exits non-zero with a usage
message; (5) existing `md-fetch <URL>` paths still pass. Also add a router unit
test for `supported_platforms()`.

**Rationale**: The operation is offline and reads static configuration, so
Constitution Principle IV (real-link integration tests) does not apply — there is
nothing to fetch. Unit coverage with `CliRunner` matches the existing CLI test
conventions (`tests/unit/test_cli.py`).

**Alternatives considered**:
- *Integration test* — no network interaction exists to exercise; rejected.

## Resolved unknowns

All Technical Context items are resolved; no `NEEDS CLARIFICATION` remains.
