# CLI Contract: mdfetch-cli

## Command Signature

```bash
md-fetch [OPTIONS] URL
```

### Positional Arguments
- `URL`: The web article URL to extract.

### Options
- `-o, --output PATH`: Write the Markdown output to the specified file path instead of standard output.
- `--retries INTEGER`: Total number of fetch attempts on transient errors (default: 3, minimum: 1).
- `--retry-delay FLOAT`: Seconds to wait between retry attempts (default: 2.0, minimum: 0).
- `--version`: Show the installed version and exit.
- `--help`: Show the usage instructions and exit.

## Exit Codes
- `0`: Success. The Markdown was printed to stdout or successfully written to the output file.
- `1` (or other non-zero): Failure. A network error occurred, the domain is unsupported, or no extractable content was found. An error message is printed to `stderr`.

## Unsupported Domain Error Format

When the URL's domain has no registered provider, the error is printed to `stderr` in this format:

```
Error: '<domain>' is not a supported platform.
Supported domains: dev.to, dzone.com, medium.com, substack.com, thenewstack.io
```

The supported-domain list is sorted alphabetically and reflects all registered providers at runtime.
