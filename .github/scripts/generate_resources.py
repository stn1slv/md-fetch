import sys
import json
import urllib.request
import re

def generate():
    for line in sys.stdin:
        line = line.strip()
        # Skip empty lines, comments, and local editable installs
        if not line or line.startswith('#') or line.startswith('-e'):
            continue
            
        # Very basic environment marker filtering to skip Windows/Linux specific packages
        if ';' in line:
            req, marker = line.split(';', 1)
            # Remove whitespace and quotes for simple matching
            marker_clean = marker.replace(' ', '').replace('"', '').replace("'", "")
            if 'sys_platform==win32' in marker_clean or 'sys_platform==linux' in marker_clean:
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
            
        url = f"https://pypi.org/pypi/{pkg}/{ver}/json"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f"# ERROR fetching {pkg}: {e}", file=sys.stderr)
            continue
        
        urls = data.get("urls", [])
        if not urls:
            print(f"# ERROR {pkg} has no urls", file=sys.stderr)
            continue
            
        # Prefer sdist (source tarball), fallback to first available wheel
        sdist = next((u for u in urls if u["packagetype"] == "sdist"), None)
        if not sdist:
            sdist = urls[0]
            
        print(f'  resource "{pkg}" do')
        print(f'    url "{sdist["url"]}"')
        print(f'    sha256 "{sdist["digests"]["sha256"]}"')
        print(f'  end\n')

if __name__ == "__main__":
    generate()
