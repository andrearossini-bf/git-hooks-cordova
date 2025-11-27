#!/usr/bin/env python3
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
ROUTE = ROOT / "www/js/route.js"
CONFIG = ROOT / "config.xml"
CHANGELOG = ROOT / "CHANGELOG.md"

def get_branch_name() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        text=True,
    ).strip()

def file_is_staged(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"],
        text=True,
    )
    for line in out.splitlines():
        if line.strip().replace("\\", "/") == rel:
            return True
    return False

def get_version_route(text: str) -> Optional[str]:
    m = re.search(r'FCIC_CONFIG\.VERSION\s*=\s*"([^"]+)"', text)
    return m.group(1) if m else None

def get_version_config(text: str) -> Optional[str]:
    m = re.search(r'<widget[^>]*\bversion="([^"]+)"', text)
    return m.group(1) if m else None

def main() -> int:
    route_staged = file_is_staged(ROUTE)
    config_staged = file_is_staged(CONFIG)

    # Se nessuno dei due è nello staged, non c'è niente da controllare
    if not (route_staged or config_staged):
        print("✓ Version consistency check skipped (version files not staged)")
        return 0

    try:
        route_text = ROUTE.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("✗ www/js/route.js non trovato", file=sys.stderr)
        return 1

    try:
        config_text = CONFIG.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("✗ config.xml non trovato", file=sys.stderr)
        return 1

    v_route = get_version_route(route_text)
    v_config = get_version_config(config_text)

    if not v_route:
        print("✗ FCIC_CONFIG.VERSION non trovata in www/js/route.js", file=sys.stderr)
        return 1
    if not v_config:
        print("✗ attributo version non trovato in config.xml", file=sys.stderr)
        return 1

    if v_route != v_config:
        print("✗ Versioni non coerenti:", file=sys.stderr)
        print("  - route.js :", v_route, file=sys.stderr)
        print("  - config.xml:", v_config, file=sys.stderr)
        return 1

    print("✓ Versioni coerenti ({}) tra route.js e config.xml".format(v_route))

    # --- Nuovo controllo: versione presente nel CHANGELOG ---
    try:
        changelog_text = CHANGELOG.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("✗ CHANGELOG.md non trovato", file=sys.stderr)
        return 1

    if v_route not in changelog_text:
        print(f"✗ CHANGELOG.md non contiene la versione {v_route}", file=sys.stderr)
        return 1

    print(f"✓ CHANGELOG contiene la versione {v_route}")
    
    # --- Nuovo controllo: versione nel nome del branch ---
    branch = get_branch_name()

    if v_route not in branch:
        print(f"✗ Il nome del branch '{branch}' non contiene la versione {v_route}", file=sys.stderr)
        return 1

    print(f"✓ Il branch '{branch}' contiene la versione {v_route}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
