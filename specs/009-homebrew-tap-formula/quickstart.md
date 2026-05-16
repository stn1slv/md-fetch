# Quickstart: Develop and Test the Homebrew Formula

**Branch**: `009-homebrew-tap-formula` | **Date**: 2026-05-16

## Prerequisites

- Homebrew installed (`/opt/homebrew/bin/brew` on Apple Silicon, `/usr/local/bin/brew` on Intel)
- Access to `stn1slv/homebrew-tap` repository with write permissions
- `HOMEBREW_TAP_TOKEN` PAT created with `contents:write` scope on `stn1slv/homebrew-tap`

## Step 1: Get the mdfetch 0.5.0 sdist URL and SHA-256

Before writing the initial formula, fetch the exact sdist path from PyPI:

```bash
curl -s https://pypi.org/pypi/mdfetch/0.5.0/json | \
  python3 -c "
import sys, json
d = json.load(sys.stdin)
for u in d['urls']:
    if u['packagetype'] == 'sdist':
        print('url:', u['url'])
        print('sha256:', u['digests']['sha256'])
"
```

## Step 2: Create the formula file

Use the skeleton in `contracts/formula.md`:

1. Replace `<hash-path>` and `<mdfetch-0.5.0-sdist-sha256>` with values from Step 1
2. Create `Formula/md-fetch.rb` in the `stn1slv/homebrew-tap` repo

## Step 3: Test the formula locally

```bash
# Install from local file (before pushing to tap)
brew install --build-from-source ./Formula/md-fetch.rb

# Verify binary works
md-fetch --version
brew test md-fetch

# Audit the formula for style issues
brew audit --strict --new Formula/md-fetch.rb
```

## Step 4: Test the tap-update CI job locally

Simulate the tap-update script with a specific version:

```bash
export VERSION="0.5.0"
export HOMEBREW_TAP_TOKEN="<your-pat>"

# Fetch sdist info
RESPONSE=$(curl -sf "https://pypi.org/pypi/mdfetch/${VERSION}/json")
SDIST_URL=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); urls=[u for u in d['urls'] if u['packagetype']=='sdist']; print(urls[0]['url'])")
SHA256=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); urls=[u for u in d['urls'] if u['packagetype']=='sdist']; print(urls[0]['digests']['sha256'])")

echo "URL:    $SDIST_URL"
echo "SHA256: $SHA256"
```

## Step 5: Add the `HOMEBREW_TAP_TOKEN` secret

1. Create a GitHub PAT at Settings → Developer settings → Personal access tokens
   - Scopes: `repo` (or fine-grained `contents:write` on `stn1slv/homebrew-tap`)
2. Add to `stn1slv/md-fetch` → Settings → Secrets and variables → Actions
   - Name: `HOMEBREW_TAP_TOKEN`

## Step 6: Trigger a test release

After the formula and CI job are merged to `main`, create a test release tag on the `main` branch of `md-fetch` to verify the end-to-end flow.
