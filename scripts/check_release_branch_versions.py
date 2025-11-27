#!/usr/bin/env python3
import subprocess
import sys
import re

# File di versione (path relativi alla root della repo)
CHANGELOG_FILE = "CHANGELOG.md"
VERSION_FILES = [
    "www/js/route.js",
    "config.xml",
    CHANGELOG_FILE,
]

# Pattern che identificano le righe "di versione"
VERSION_PATTERNS = {
    "www/js/route.js": re.compile(r"FCIC_CONFIG\.VERSION"),
    "config.xml": re.compile(r"<widget[^>]*\bversion="),
}

def get_branch() -> str:
    out = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        text=True,
    )
    return out.strip()

def get_staged_files() -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"],
        text=True,
    )
    return [line.strip() for line in out.splitlines() if line.strip()]

def file_touches_version(path: str) -> bool:
    """
    Ritorna True se nello STAGED diff di `path` vengono toccate righe
    che contengono la versione (secondo VERSION_PATTERNS).
    """
    pattern = VERSION_PATTERNS.get(path)
    if pattern is None:
        return False

    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "-U0", "--", path],
            text=True,
        )
    except subprocess.CalledProcessError:
        # Se il diff fallisce, non blocchiamo a sproposito
        return False

    for line in out.splitlines():
        # Consideriamo solo le righe effettivamente cambiate
        if not line or line[0] not in {"+", "-"}:
            continue
        if line.startswith("+++ ") or line.startswith("--- "):
            continue
        if pattern.search(line):
            return True

    return False

def main() -> int:
    branch = get_branch()
    staged_files = get_staged_files()
    staged_set = {f.replace("\\", "/") for f in staged_files}

    if branch.startswith("release/"):
        # Su release/*: TUTTI i file di versione DEVONO essere nello staged
        missing = [f for f in VERSION_FILES if f not in staged_set]
        if missing:
            print(f"✗ Sei su '{branch}': il commit di rilascio deve includere anche:", file=sys.stderr)
            for f in missing:
                print(f"  - {f}", file=sys.stderr)
            print(f"Suggerimento: esegui `git add {' '.join(VERSION_FILES)}` prima di committare.", file=sys.stderr)
            return 1
    else:
        # Su altri branch:
        # - vietato cambiare la versione in route.js/config.xml
        # - vietato toccare CHANGELOG.md in assoluto
        forbidden_files = []

        for f in VERSION_FILES:
            if f == CHANGELOG_FILE:
                if f in staged_set:
                    forbidden_files.append(f)
            else:
                if f in staged_set and file_touches_version(f):
                    forbidden_files.append(f)

        if forbidden_files:
            print("✗ Puoi modificare route.js/config.xml/CHANGELOG.md solo per il bump versione su branch release/*", file=sys.stderr)
            print(f"Branch attuale: {branch}", file=sys.stderr)
            print("File non permessi in questo commit:", file=sys.stderr)
            for f in forbidden_files:
                print(f"  - {f}", file=sys.stderr)
            return 1

    # Se arrivi qui, tutto ok
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
