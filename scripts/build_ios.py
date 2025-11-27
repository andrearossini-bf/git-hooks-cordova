#!/usr/bin/env python3
import re
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"

ROUTE = ROOT / "www/js/route.js"

DEFAULT_XCODE_PATH = "/Applications/Xcode.app/Contents/MacOS/Xcode"
WORKSPACE_PATH = ROOT / "platforms/ios/Intelliclima+.xcworkspace"

def load_dotenv():
    """Carica .env se esiste (solo righe KEY=VALUE, no dipendenze esterne)."""
    if not ENV_FILE.exists():
        return

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key and key not in os.environ:
            os.environ[key] = value.strip()

def run(cmd, allow_fail=False):
    """Esegue un comando, esce con errore se fallisce (a meno di allow_fail=True)."""
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0 and not allow_fail:
        print(f"✗ Command failed: {' '.join(cmd)}", file=sys.stderr)
        sys.exit(result.returncode)
    return result.returncode

def get_branch() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        text=True
    ).strip()
    
def set_versione_produzione(value: bool):
    """
    Imposta var _versioneProduzione = true/false in route.js
    """
    text = ROUTE.read_text(encoding="utf-8")

    replacement = f"var _versioneProduzione = {'true' if value else 'false'};"

    new_text, count = re.subn(
        r"var _versioneProduzione\s*=\s*(true|false);",
        replacement,
        text
    )

    if count == 0:
        print("✗ Non ho trovato '_versioneProduzione' in route.js", file=sys.stderr)
        sys.exit(1)

    ROUTE.write_text(new_text, encoding="utf-8")
    print(f"✔ _versioneProduzione impostato a {value}")
    
def force_kill_xcode():
    print("Forcing Xcode to quit...")

    subprocess.run(
        ["killall", "-9", "Xcode"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("✔ Xcode process killed (if it was running)")

def main() -> int:
    branch = get_branch()

    # Esegui solo su branch tipo:
    #   release/*android*
    if not (branch.startswith("release/") and "ios" in branch.lower()):
        print(f"Skipping iOS build (branch {branch} is not release/* with 'ios' in the name)")
        return 0
    
    # Chiudi Xcode se è aperto
    force_kill_xcode()
    
    # ----------------- Xcode path: .env > default -----------------
    load_dotenv()
    xcode_path = os.environ.get("XCODE_PATH") or DEFAULT_XCODE_PATH
    xcode_path = os.path.expanduser(xcode_path)

    print(f"Using Xcode path: {xcode_path}")

    # ----------------- Cordova: remove platforms -----------------
    # Se la piattaforma non esiste, non vogliamo fallire per quello.
    run(["cordova", "platform", "remove", "ios"], allow_fail=True)
    run(["cordova", "platform", "remove", "android"], allow_fail=True)

    for rel in ("builds","node_modules", "platforms", "plugins"):
        path = ROOT / rel
        if path.exists():
            print(f"Removing {path}")
            shutil.rmtree(path, ignore_errors=True)
    
    # Metti _versioneProduzione = true
    set_versione_produzione(True)

    # ----------------- Add iOS platform -----------------
    run(["cordova", "platform", "add", "ios@7"])

    # ----------------- Apri Xcode -----------------
    if not WORKSPACE_PATH.exists():
        print(f"✗ Workspace non trovato: {WORKSPACE_PATH}", file=sys.stderr)
        return 1

    try:
        # Lanciamo Xcode in background, come nello script bash (&> /dev/null &)
        subprocess.Popen(
            [xcode_path, str(WORKSPACE_PATH)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print(f"✗ Xcode non trovato in: {xcode_path}", file=sys.stderr)
        return 1

    print("✅ iOS project recreated and Xcode launched")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
