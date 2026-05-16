# Data Model: Homebrew Tap Formula

**Branch**: `009-homebrew-tap-formula` | **Date**: 2026-05-16

## Entities

### Homebrew Formula (`Formula/md-fetch.rb`)

**Repository**: `stn1slv/homebrew-tap`  
**Type**: Ruby source file (Homebrew DSL)

| Field | Type | Description |
|-------|------|-------------|
| `url` | String | PyPI sdist tarball URL, e.g. `https://files.pythonhosted.org/.../mdfetch-{version}.tar.gz` |
| `sha256` (package) | String | Hex SHA-256 of the sdist tarball |
| `version` | String | Derived from the sdist URL by Homebrew; must match PyPI version |
| `license` | String | `"MIT"` (static) |
| `depends_on` | String | `"python@3.12"` (static, unless minimum Python version changes) |
| `resource[].name` | String | Dependency package name (e.g. `"anyio"`) |
| `resource[].url` | String | PyPI sdist URL for the dependency at pinned version |
| `resource[].sha256` | String | Hex SHA-256 of the dependency sdist |

**Mutable fields per release**: `url` (package) and `sha256` (package) change on every release.  
**Static fields**: `license`, `depends_on`, all `resource` blocks (dependency versions are bumped only on manual dep upgrades, not on mdfetch releases).

---

### PyPI Release Metadata

**Source**: PyPI JSON API — `https://pypi.org/pypi/mdfetch/{version}/json`

Relevant fields from the API response:

| Field path | Type | Description |
|------------|------|-------------|
| `.info.version` | String | Published version string |
| `.urls[].packagetype` | String | `"sdist"` or `"bdist_wheel"` |
| `.urls[].url` | String | Download URL for this distribution file |
| `.urls[].digests.sha256` | String | Hex SHA-256 checksum |

**Selection rule**: select the entry where `packagetype == "sdist"`.

---

### Tap-Update Job Environment

Inputs consumed by the `update-homebrew-tap` GitHub Actions job:

| Variable | Source | Description |
|----------|--------|-------------|
| `GITHUB_REF_NAME` | GitHub Actions context | Release tag, e.g. `v0.5.0` |
| `TAP_GITHUB_TOKEN` | Repository secret | PAT with `contents:write` on `stn1slv/homebrew-tap` |
| `VERSION` | Derived (`${GITHUB_REF_NAME#v}`) | Version without `v` prefix, e.g. `0.5.0` |
| `SDIST_URL` | PyPI JSON API | Full URL of the new sdist tarball |
| `SHA256` | PyPI JSON API | SHA-256 of the new sdist tarball |

---

### README Changes

Two README files are modified:

| File | Repository | Change |
|------|-----------|--------|
| `README.md` | `stn1slv/md-fetch` | Add `brew install stn1slv/tap/md-fetch` as secondary install option below `pip install mdfetch` |
| `README.md` | `stn1slv/homebrew-tap` | Add `md-fetch` row to the Available Formulas table |
