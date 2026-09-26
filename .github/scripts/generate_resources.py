import argparse
import json
import sys
import urllib.request

from packaging.markers import Marker, default_environment


def target_environment(python_version):
    """Marker environment of the Homebrew install: macOS with the formula's Python."""
    env = default_environment()
    env.update(
        python_version=python_version,
        python_full_version=f"{python_version}.0",
        sys_platform="darwin",
        platform_system="Darwin",
        os_name="posix",
    )
    return env


def generate(python_version):
    env = target_environment(python_version)
    seen = {}
    for line in sys.stdin:
        line = line.strip()
        # Skip empty lines, comments, and local editable installs
        if not line or line.startswith('#') or line.startswith('-e'):
            continue
            
        # Keep only requirements whose environment marker holds for the Homebrew
        # install. A lock resolved for several Python versions lists some
        # packages once per version range, e.g. anyio for < 3.15 and >= 3.15.
        if ';' in line:
            req, marker = line.split(';', 1)
            if not Marker(marker.strip()).evaluate(env):
                continue
            line = req.strip()
        
        # We only care about pinned packages
        if '==' not in line:
            continue
            
        pkg, ver = line.split('==', 1)
        pkg = pkg.strip()
        ver = ver.strip()
        
        # We don't need a resource block for mdfetch itself
        if pkg == "mdfetch":
            continue

        # Homebrew keeps only the first resource of a given name, so a second
        # one would be dropped silently. Fail instead of guessing.
        if pkg in seen:
            print(
                f"ERROR: {pkg} is pinned twice ({seen[pkg]} and {ver}) for Python {python_version}",
                file=sys.stderr,
            )
            sys.exit(1)
        seen[pkg] = ver
            
        url = f"https://pypi.org/pypi/{pkg}/{ver}/json"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f"ERROR: Failed fetching {pkg}: {e}", file=sys.stderr)
            sys.exit(1)
        
        urls = data.get("urls", [])
        if not urls:
            print(f"ERROR: {pkg} has no urls on PyPI", file=sys.stderr)
            sys.exit(1)
            
        # Require sdist (source tarball) to ensure architecture independence
        sdist = next((u for u in urls if u["packagetype"] == "sdist"), None)
        if not sdist:
            print(f"ERROR: {pkg} has no sdist (source tarball) available on PyPI", file=sys.stderr)
            sys.exit(1)
            
        print(f'  resource "{pkg}" do')
        print(f'    url "{sdist["url"]}"')
        print(f'    sha256 "{sdist["digests"]["sha256"]}"')
        print(f'  end\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Homebrew resource blocks from `uv export` output on stdin."
    )
    parser.add_argument("--python", required=True, help="Python version of the formula, e.g. 3.13")
    generate(parser.parse_args().python)
