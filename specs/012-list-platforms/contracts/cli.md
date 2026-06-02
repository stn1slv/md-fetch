# CLI Contract: `md-fetch --list-platforms`

The `md-fetch` command gains one boolean flag. The `URL` positional argument
becomes optional.

## Command surface

```
md-fetch [OPTIONS] [URL]

Options:
  --version                Show the version and exit.
  --list-platforms         List all supported platforms and exit.   [NEW]
  -o, --output PATH        Save Markdown to this file.
  --retries INTEGER        Total fetch attempts on transient errors.  [default: 3]
  --retry-delay FLOAT      Seconds between retry attempts.            [default: 2.0]
  -f, --force              Overwrite the output file if it exists.
  --help                   Show this message and exit.
```

## Behaviors

| Invocation | stdout | stderr | Exit |
|------------|--------|--------|------|
| `md-fetch --list-platforms` | Platform list (see below) | — | 0 |
| `md-fetch` (no URL, no flag) | — | Usage error: missing `URL` | 2 |
| `md-fetch <URL>` | Extracted Markdown (unchanged) | — | 0 |
| `md-fetch <bad-url>` | — | Existing error messages (unchanged) | 1 |

- `--list-platforms` takes precedence: if both `--list-platforms` and a `URL` are
  supplied, the list is printed and **no extraction occurs** (FR-008).
- `--list-platforms` performs **no network request** (FR-004).

## Output format (`--list-platforms`)

Plain text to stdout, exit 0:

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

Rules:
- Header line `Supported platforms:` followed by one indented entry per platform.
- Entries sorted ascending by domain (deterministic — FR-005).
- Multi-tenant platforms append ` (and *.<domain>)`; exact-match platforms show the
  bare domain (FR-006).
- The set of domains equals the registry exactly — no missing, no extras (SC-002).

> The exact domains shown above reflect the registry at time of writing and will
> grow automatically as providers are added.

## Acceptance checks (map to spec)

- AC1 (US1 #1): `--list-platforms` exits 0 and lists every supported domain.
- AC2 (US1 #2): no network call (assert `extract` not invoked).
- AC3 (US1 #3): a newly registered domain appears with no change to the flag code.
- AC4 (US2 #1/#2): subdomain platforms annotated; exact-match plain.
- AC5: `md-fetch` with neither URL nor flag exits 2 with a usage message.
- AC6: `md-fetch <URL>` paths remain green (no regression).
