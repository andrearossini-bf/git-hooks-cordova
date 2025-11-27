#!/usr/bin/env python3
import re
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROUTE = ROOT / "www/js/route.js"
CONFIG = ROOT / "config.xml"

DEBUG_APK_PATH = ROOT / "platforms/android/app/build/outputs/apk/debug/app-debug.apk"
RELEASE_APK_PATH = ROOT / "platforms/android/app/build/outputs/apk/release/app-release.apk"
AAB_PATH = ROOT / "platforms/android/app/build/outputs/bundle/release/app-release.aab"

BUILDS_DIR = ROOT / "builds"
ENV_FILE = ROOT / ".env"

REQUIRED_VARS = [
    "KEYSTORE_PATH",
    "KEYSTORE_PASSWORD",
    "KEY_ALIAS",
    "KEY_PASSWORD",
]

def load_dotenv():
    """Carica .env se esiste"""
    if not ENV_FILE.exists():
        return

    print("Loading .env from", ENV_FILE)

    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key not in os.environ:
            os.environ[key] = value.strip()

def get_branch() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        text=True
    ).strip()

def get_version() -> str:
    if ROUTE.exists():
        text = ROUTE.read_text(encoding="utf-8")
        m = re.search(r'FCIC_CONFIG\.VERSION\s*=\s*"([^"]+)"', text)
        if m:
            return m.group(1)

    if CONFIG.exists():
        text = CONFIG.read_text(encoding="utf-8")
        m = re.search(r'<widget[^>]*\bversion="([^"]+)"', text)
        if m:
            return m.group(1)

    print("✗ Impossibile determinare la versione", file=sys.stderr)
    sys.exit(1)

def require_env_vars():
    missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
    if missing:
        print("✗ Mancano le variabili d'ambiente:", ", ".join(missing), file=sys.stderr)
        print("Definiscile come variabili d'ambiente o nel file .env", file=sys.stderr)
        sys.exit(1)

def run(cmd):
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("✗ Command failed:", " ".join(cmd), file=sys.stderr)
        sys.exit(1)
        
def get_staged_files():
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"],
        text=True,
    )
    return {f.replace("\\", "/") for f in out.splitlines()}

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

def main():
    staged = get_staged_files()

    VERSION_FILES = {
        "www/js/route.js",
        "config.xml",
    }

    if not staged.intersection(VERSION_FILES):
        print("Skipping Android build: no version files in commit")
        return 0

    branch = get_branch()

    # Esegui solo su branch tipo:
    #   release/*android*
    if not (branch.startswith("release/") and "android" in branch.lower()):
        print(f"Skipping Android build (branch {branch} is not release/* with 'android' in the name)")
        return 0

    print("Android release build triggered on:", branch)

    # Carica .env se necessario
    load_dotenv()
    require_env_vars()

    KEYSTORE_PATH = os.environ["KEYSTORE_PATH"]
    KEYSTORE_PASSWORD = os.environ["KEYSTORE_PASSWORD"]
    KEY_ALIAS = os.environ["KEY_ALIAS"]
    KEY_PASSWORD = os.environ["KEY_PASSWORD"]

    # Remove platforms
    try:
        run(["cordova", "platform", "remove", "ios"])
        run(["cordova", "platform", "remove", "android"])
    except SystemExit:
        print("Warning: impossibile rimuovere piattaforma android, continuo comunque")
    
    # Clean builds and Cordova artifacts (ma NON node_modules)
    for path in [BUILDS_DIR, ROOT / "node_modules", ROOT / "platforms", ROOT / "plugins"]:
        if path.exists():
            print(f"Removing {path}")
            shutil.rmtree(path, ignore_errors=True)

    # Add platform
    run(["cordova", "platform", "add", "android@14"])
    
    # 1. Metti _versioneProduzione = false
    set_versione_produzione(False)
    
    # Build debug APK
    run([
        "cordova", "build", "android", "--debug"
    ])
    
    # 1. Metti _versioneProduzione = true
    set_versione_produzione(True)

    # Build release APK
    run([
        "cordova", "build", "android", "--release",
        "--",
        f"--keystore={KEYSTORE_PATH}",
        f"--storePassword={KEYSTORE_PASSWORD}",
        f"--alias={KEY_ALIAS}",
        f"--password={KEY_PASSWORD}",
        "--packageType=apk"
    ])

    # Build release AAB
    run([
        "cordova", "build", "android", "--release",
        "--",
        f"--keystore={KEYSTORE_PATH}",
        f"--storePassword={KEYSTORE_PASSWORD}",
        f"--alias={KEY_ALIAS}",
        f"--password={KEY_PASSWORD}",
        "--packageType=bundle"
    ])

    version = get_version()
    print("✔ Version detected:", version)

    BUILDS_DIR.mkdir(exist_ok=True)

    debug_apk_target = BUILDS_DIR / f"app-debug-test.{version}.apk"
    release_apk_target = BUILDS_DIR / f"app-release-prod.{version}.apk"
    aab_target = BUILDS_DIR / f"app-release-prod.{version}.aab"

    if DEBUG_APK_PATH.exists():
        shutil.copy2(DEBUG_APK_PATH, debug_apk_target)
        print("✔ Debug APK copied to:", debug_apk_target)
    else:
        print("✗ Debug APK not found:", DEBUG_APK_PATH)
        
    if RELEASE_APK_PATH.exists():
        shutil.copy2(RELEASE_APK_PATH, release_apk_target)
        print("✔ Release APK copied to:", release_apk_target)
    else:
        print("✗ Release APK not found:", RELEASE_APK_PATH)

    if AAB_PATH.exists():
        shutil.copy2(AAB_PATH, aab_target)
        print("✔ AAB copied to:", aab_target)
    else:
        print("✗ AAB not found:", AAB_PATH)

    print("✅ Android build completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
