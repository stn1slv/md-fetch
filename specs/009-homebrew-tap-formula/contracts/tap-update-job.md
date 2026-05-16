# Contract: Tap-Update CI Job (`update-homebrew-tap`)

**Workflow file**: `.github/workflows/publish.yml` in `stn1slv/md-fetch`  
**Date**: 2026-05-16

## Job Summary

A new `update-homebrew-tap` job is added to `publish.yml`, running after the existing `publish` job succeeds. It fetches the new release's sdist SHA-256 from PyPI, clones the homebrew-tap repo, patches the formula, and pushes the commit.

## Job Definition Skeleton

```yaml
update-homebrew-tap:
  name: Update Homebrew tap
  runs-on: ubuntu-latest
  needs: publish
  permissions:
    contents: read

  steps:
    - name: Fetch sdist info from PyPI (with retry)
      env:
        VERSION: ${{ github.ref_name }}  # e.g. v0.5.1
      run: |
        VERSION="${VERSION#v}"           # strip leading 'v'
        SHA256=""
        for i in 1 2 3; do
          RESPONSE=$(curl -sf "https://pypi.org/pypi/mdfetch/${VERSION}/json" || true)
          if [ -n "$RESPONSE" ]; then
            SDIST_URL=$(echo "$RESPONSE" | python3 -c \
              "import sys,json; d=json.load(sys.stdin); \
               urls=[u for u in d['urls'] if u['packagetype']=='sdist']; \
               print(urls[0]['url'] if urls else '')" 2>/dev/null || true)
            SHA256=$(echo "$RESPONSE" | python3 -c \
              "import sys,json; d=json.load(sys.stdin); \
               urls=[u for u in d['urls'] if u['packagetype']=='sdist']; \
               print(urls[0]['digests']['sha256'] if urls else '')" 2>/dev/null || true)
            if [ -n "$SHA256" ] && [ -n "$SDIST_URL" ]; then break; fi
          fi
          echo "PyPI not ready, retrying in 30s (attempt $i/3)..."
          sleep 30
        done
        if [ -z "$SHA256" ]; then
          echo "ERROR: Could not fetch sdist info from PyPI after 3 retries" >&2; exit 1
        fi
        echo "SDIST_URL=${SDIST_URL}" >> "$GITHUB_ENV"
        echo "SHA256=${SHA256}"       >> "$GITHUB_ENV"
        echo "VERSION=${VERSION}"     >> "$GITHUB_ENV"

    - name: Clone homebrew-tap and update formula
      env:
        TAP_GITHUB_TOKEN: ${{ secrets.TAP_GITHUB_TOKEN }}
      run: |
        git clone "https://x-access-token:${TAP_GITHUB_TOKEN}@github.com/stn1slv/homebrew-tap.git"
        cd homebrew-tap
        git config user.name  "github-actions[bot]"
        git config user.email "github-actions[bot]@users.noreply.github.com"

        # Replace the main package url and sha256 lines
        sed -i "s|  url \"https://files.pythonhosted.org/packages/.*/mdfetch-.*\.tar\.gz\"|  url \"${SDIST_URL}\"|" \
          Formula/md-fetch.rb
        sed -i "0,/  sha256 \"[a-f0-9]*\"/{s|  sha256 \"[a-f0-9]*\"|  sha256 \"${SHA256}\"|}" Formula/md-fetch.rb

        git add Formula/md-fetch.rb
        git commit -m "chore: bump md-fetch to v${VERSION}"
        git pull --rebase
        git push
```

## Failure Modes and Expected Behavior

| Failure | Job Behaviour |
|---------|--------------|
| PyPI returns 404 for new version after 3×30s retries | Step exits non-zero → job fails → workflow shows red |
| `TAP_GITHUB_TOKEN` absent or invalid | `git clone` or `git push` exits non-zero → job fails |
| `sed` finds no matching line (formula structure changed) | `git diff --quiet` would show no changes; `git commit` would fail — job exits non-zero |
| Push conflict (concurrent release) | `git pull --rebase` resolves sequential conflicts; true concurrent failure exits non-zero |

## Prerequisites

- `TAP_GITHUB_TOKEN` secret must be set in `stn1slv/md-fetch` repository settings.
- Token requires: `contents:write` scope on `stn1slv/homebrew-tap`.
- `jq` is **not** required — Python 3 (always available on `ubuntu-latest`) is used for JSON parsing.
