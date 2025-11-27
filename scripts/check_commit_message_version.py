#!/usr/bin/env python3
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
ROUTE = ROOT / "www/js/route.js"
CONFIG = ROOT / "config.xml"

VERSION_FILES = {
    "www/js/route.js",
    "config.xml",
    "CHANGELOG.md",
}

def get_branch_name() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        text=True,
    ).strip()

def get_staged_files() -> set[str]:
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"],
        text=True,
    )
    return {line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()}

def get_version_route(text: str) -> Optional[str]:
    m = re.search(r'FCIC_CONFIG\.VERSION\s*=\s*"([^"]+)"', text)
    return m.group(1) if m else None

def get_version_config(text: str) -> Optional[str]:
    m = re.search(r'<widget[^>]*\bversion="([^"]+)"', text)
    return m.group(1) if m else None

def main() -> int:
    # Il path al file con il messaggio di commit è il primo argomento
    if len(sys.argv) < 2:
        print("✗ Nessun file di commit message passato allo hook commit-msg", file=sys.stderr)
        return 1

    commit_msg_path = Path(sys.argv[1])

    branch = get_branch_name()

    # Esegui solo sui branch di release
    if not branch.startswith("release/"):
        print(f"Skipping commit message version check on non-release branch: {branch}")
        return 0

    # Esegui il controllo solo se nel commit ci sono i file di versione/changelog
    staged = get_staged_files()
    if not staged.intersection(VERSION_FILES):
        print("Skipping commit message version check (no version/changelog files in commit)")
        return 0

    # Leggi versione da route/config
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
        print("✗ Versioni non coerenti tra route.js e config.xml, commit message check abortito", file=sys.stderr)
        return 1

    # Leggi messaggio di commit
    try:
        commit_msg = commit_msg_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"✗ File commit message non trovato: {commit_msg_path}", file=sys.stderr)
        return 1

    if v_route not in commit_msg:
        print(f"✗ Il messaggio di commit non contiene la versione {v_route}", file=sys.stderr)
        print("  Suggerimento: includi la versione nel commit, ad esempio:", file=sys.stderr)
        print(f"    \"release android {v_route}\"", file=sys.stderr)
        return 1

    print(f"✓ Commit message contiene la versione {v_route}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
