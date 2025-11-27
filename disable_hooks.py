#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = ROOT / "tools" / "my-hooks"

def run(cmd):
    print(">", " ".join(cmd))
    result = subprocess.run(cmd, shell=(sys.platform == "win32"))
    if result.returncode != 0:
        print(f"✗ Command failed: {' '.join(cmd)}")
        sys.exit(result.returncode)

def main():
    print("🔧 Disabling local git hooks...")

    # Controlla il valore attuale
    current = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        shell=(sys.platform == "win32"),
    ).stdout.strip()

    if not current:
        print("ℹ core.hooksPath non è impostato. Nulla da disabilitare.")
        return 0

    if Path(current).resolve() != HOOK_PATH.resolve():
        print(f"⚠ core.hooksPath è impostato su: {current}")
        print("  Non sembra essere il tuo tools/my-hooks. Non lo tocco.")
        return 0

    # Rimuove l'impostazione
    run(["git", "config", "--unset", "core.hooksPath"])

    print("✅ Hook locali disabilitati!")
    print("Git ora usa di nuovo .git/hooks standard")
    return 0

if __name__ == "__main__":
    sys.exit(main())
