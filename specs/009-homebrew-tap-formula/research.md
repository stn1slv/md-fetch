# Research: Homebrew Tap Formula

**Branch**: `009-homebrew-tap-formula` | **Date**: 2026-05-16

## Decision 1: Formula Pattern for Python CLIs

**Decision**: Use Homebrew's `Language::Python::Virtualenv` mixin (`include Language::Python::Virtualenv`).

**Rationale**: This is the canonical Homebrew pattern for Python CLI tools. It creates an isolated Python virtualenv inside the Cellar, installs the package and all declared `resource` blocks into it, and symlinks the `md-fetch` entry-point script into `bin/`. The result is a fully self-contained installation — users need neither an existing Python environment nor `pip`.

**Alternatives considered**:
- Distributing a pre-built binary (not viable; mdfetch is a pure Python package with no binary build infrastructure).
- Using `pipx` as the install mechanism (non-standard for Homebrew; forces dependency on pipx being installed).

---

## Decision 2: Dependency Resource Blocks

**Decision**: Declare all transitive runtime dependencies as `resource` blocks in the formula with pinned versions and SHA-256 checksums taken from `uv.lock`.

**Rationale**: Homebrew's virtualenv mixin requires all dependencies to be explicitly declared because it does not run `pip install -r` from PyPI at install time — every resource must be present as a pre-fetched tarball. Pinning to the exact versions currently in `uv.lock` ensures reproducibility.

**Pinned resource versions and hashes** (sdist sources from PyPI):

| Package | Version | sdist SHA-256 |
|---------|---------|---------------|
| anyio | 4.13.0 | `334b70e641fd2221c1505b3890c69882fe4a2df910cba14d97019b90b24439dc` |
| beautifulsoup4 | 4.14.3 | `6292b1c5186d356bba669ef9f7f051757099565ad9ada5dd630bd9de5fa7fb86` |
| certifi | 2026.4.22 | `8d455352a37b71bf76a79caa83a3d6c25afee4a385d632127b6afb3963f1c580` |
| click | 8.3.3 | `398329ad4837b2ff7cbe1dd166a4c0f8900c3ca3a218de04466f38f6497f18a2` |
| h11 | 0.16.0 | `4e35b956cf45792e4caa5885e69fba00bdbc6ffafbfa020300e549b208ee5ff1` |
| httpcore | 1.0.9 | `6e34463af53fd2ab5d807f399a9b45ea31c3dfa2276f15a2c3f00afff6e176e8` |
| httpx | 0.28.1 | `75e98c5f16b0f35b567856f597f06ff2270a374470a5c2392242528e3e3e42fc` |
| idna | 3.15 | `ca962446ea538f7092a95e057da437618e886f4d349216d2b1e294abfdb65fdc` |
| lxml | 6.1.0 | `bfd57d8008c4965709a919c3e9a98f76c2c7cb319086b3d26858250620023b13` |
| markdownify | 1.2.2 | `b274f1b5943180b031b699b199cbaeb1e2ac938b75851849a31fd0c3d6603d09` |
| six | 1.17.0 | `ff70335d468e7eb6ec65b95b99d3a2836546063f63acc5171de367e834932a81` |
| soupsieve | 2.8.3 | `3267f1eeea4251fb42728b6dfb746edc9acaffc4a45b27e19450b676586e8349` |
| typing-extensions | 4.15.0 | `0cea48d173cc12fa28ecabc3b837ea3cf6f38c6d1136f85cbaaf598984861466` |

**Exclusions**:
- `colorama` — click dependency only on `sys_platform == 'win32'`; Homebrew targets macOS/Linux, so excluded.
- All dev-only packages (`pytest`, `ruff`, `mypy`, etc.) — not runtime dependencies.

**mdfetch sdist URL template**: `https://files.pythonhosted.org/packages/{hash-path}/mdfetch-{version}.tar.gz`  
The exact path component and SHA-256 for v0.5.0 must be obtained from PyPI at implementation time (package not yet published at plan time).

---

## Decision 3: PyPI JSON API for SHA-256 Fetching

**Decision**: Use the versioned PyPI JSON API endpoint to fetch the sdist SHA-256.

**Endpoint**: `https://pypi.org/pypi/mdfetch/{version}/json`

**Response path**: `.urls[] | select(.packagetype == "sdist") | {url, sha256: .digests.sha256}`

**Retry strategy** (per FR-005 clarification): poll the endpoint up to 3 times with 30-second sleep intervals before failing. This handles PyPI propagation delay between upload confirmation and JSON API availability.

**Implementation sketch**:
```bash
for i in 1 2 3; do
  RESPONSE=$(curl -sf "https://pypi.org/pypi/mdfetch/${VERSION}/json")
  if [ $? -eq 0 ]; then
    SDIST_URL=$(echo "$RESPONSE" | jq -r '.urls[] | select(.packagetype=="sdist") | .url')
    SHA256=$(echo "$RESPONSE" | jq -r '.urls[] | select(.packagetype=="sdist") | .digests.sha256')
    if [ -n "$SHA256" ]; then break; fi
  fi
  echo "PyPI not ready, retrying in 30s (attempt $i/3)..."
  sleep 30
done
[ -z "$SHA256" ] && { echo "ERROR: PyPI did not serve new release after 3 retries"; exit 1; }
```

---

## Decision 4: Tap-Update Commit Identity

**Decision**: Use the GITHUB_ACTIONS bot identity for the tap-update commit (`github-actions[bot]`).

**Rationale**: Standard practice for automated GitHub Actions commits. Avoids attributing bot commits to the maintainer's personal identity. The PAT is still required for authentication/push rights, but the commit author can be set to the bot identity.

**Git config**:
```bash
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
```

---

## Decision 5: Formula Update Mechanism

**Decision**: Use `sed` in-place substitution to update the version string and SHA-256 in the formula file.

**Rationale**: The formula has exactly two fields that change per release: the `url` line (contains the version) and the `sha256` line immediately following the `url`. A targeted sed replacement on these two lines is simpler and less error-prone than a Python script or Ruby parser.

**Pattern** (the formula's main package block has the version in the url and sha256 on the next line):
```bash
# Update sdist URL
sed -i "s|url \"https://files.pythonhosted.org/packages/.*/mdfetch-.*\.tar\.gz\"|url \"${SDIST_URL}\"|" Formula/md-fetch.rb
# Update SHA256
sed -i "s/sha256 \"[a-f0-9]*\"/sha256 \"${SHA256}\"/" Formula/md-fetch.rb
```

**Concurrent release safety**: If two releases happen simultaneously, the second tap-update job may encounter a push conflict. The job uses `git pull --rebase` before pushing to handle this case gracefully for sequential releases. Simultaneous concurrent releases are considered out of scope (single-maintainer project).

---

## Decision 6: Homebrew Tap README Update

**Decision**: Add `md-fetch` to the `Available Formulas` table in `stn1slv/homebrew-tap/README.md`.

**Row to add**:
```markdown
| [md-fetch](https://github.com/stn1slv/md-fetch) | Extract article content from web platforms as clean Markdown |
```
