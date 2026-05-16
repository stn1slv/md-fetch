# CLI Contract: mdfetch-cli

## Command Signature

```bash
md-fetch [OPTIONS] URL
```

### Positional Arguments
- `URL`: The web article URL to extract.

### Options
- `-o, --output PATH`: Write the Markdown output to the specified file path instead of standard output.
- `--help`: Show the usage instructions and exit.

## Exit Codes
- `0`: Success. The Markdown was printed to stdout or successfully written to the output file.
- `1` (or other non-zero): Failure. A network error occurred, the domain is unsupported, or no extractable content was found. An error message is printed to `stderr`.
