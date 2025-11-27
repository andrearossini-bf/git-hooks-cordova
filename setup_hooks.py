#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

# Ora il root è due livelli sopra: repo-cliente/
ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = ROOT / "tools" / "my-hooks-cordova"

def run(cmd, allow_fail=False):
    print(">", " ".join(cmd))
    result = subprocess.run(cmd, shell=(sys.platform == "win32"))
    if result.returncode != 0 and not allow_fail:
        print(f"✗ Command failed: {' '.join(cmd)}")
        sys.exit(result.returncode)

def main():
    print("🔧 Enabling local git hooks from:", HOOK_PATH)

    if not HOOK_PATH.exists():
        print("✗ tools/my-hooks-cordova not found. Hai clonato il repo degli hook?")
        return 1

    print("🔧 Setting git core.hooksPath...")

    run(["git", "config", "core.hooksPath", str(HOOK_PATH)])

    print("✅ Local hooks enabled!")
    print(f"Git ora usa gli hook in: {HOOK_PATH}")
    print("ℹ Repo cliente rimane completamente pulita.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
