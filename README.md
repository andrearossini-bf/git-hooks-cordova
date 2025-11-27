# git-hooks-cordova — Hook Git personalizzati per Cordova

Questo repository contiene un set di *git hooks* personalizzati e automatismi pensati per gestire release e build del progetto (version bump, build Android/iOS, controlli di coerenza, ecc.), senza sporcare il repository principale del cliente.

---

## 🎯 Obiettivo

Permettere di:

- **gestire versioning, changelog e build in modo sicuro** (Android / iOS)
- **garantire coerenza** tra versione su codice, config, branch, changelog e commit message
- far sì che la **repo del cliente rimanga pulita**: nessun file di configurazione committato, nessuno script di build
- avere un sistema **facile da attivare e disattivare** in locale

---

## 🚀 Utilizzo degli hook

### Qualsiasi branch

- Bloccati i commit che includono modifiche alle **versioni** (`FCIC_CONFIG.VERSION` in `route.js`, attributo `version` in `config.xml`)
- Bloccati i commit che toccano `CHANGELOG.md` al di fuori dei branch `release/*`
- Su branch non di release puoi ancora modificare `route.js` / `config.xml`, ma **non** le righe di versione

### Branch `release/*-<version>`

Prima di ogni commit:

- Controllata la coerenza delle versioni tra:
  - `www/js/route.js`
  - `config.xml`
  - `CHANGELOG.md`
  - nome del branch (`release/...<version>...`)
  - messaggio di commit (deve contenere la versione)
- Bloccato il commit se uno di questi elementi non contiene la **stessa versione**.

### Branch `release/android-<version>`

- Eseguita la build Android **prima del commit**:
  - build `--debug` con `_versioneProduzione = false`
  - build `--release` (APK + AAB) con `_versioneProduzione = true`
- Se la build fallisce → **commit bloccato**
- Nella cartella `builds/` vengono prodotti:
  - `app-debug-test.<version>.apk`
  - `app-release-prod.<version>.apk`
  - `app-release-prod.<version>.aab`

### Branch `release/ios-<version>`

- Ricreata la piattaforma iOS (rimozione/aggiunta piattaforma Cordova)
- Forzata la chiusura di Xcode (per evitare conflitti) e riaperto il workspace del progetto
- Se qualcosa va storto (comandi Cordova, workspace mancante, Xcode non trovato) → **commit bloccato**

### Requisiti / prerequisiti

- Variabili d’ambiente o `.env` configurati per:
  - `KEYSTORE_PATH`, `KEYSTORE_PASSWORD`, `KEY_ALIAS`, `KEY_PASSWORD` (build Android)
  - eventuale `XCODE_PATH` custom (se non si usa quello di default)
- Gli hook girano **solo** se nel commit sono presenti i file di versione/changelog
  (`www/js/route.js`, `config.xml`, `CHANGELOG.md`), per non rallentare i commit "normali".

---

## 🚀 Installazione degli hook

### 1. Clonare il repo del cliente

```bash
git clone <repo-cliente>
cd <repo-cliente>
```

### 2. Scaricare i hook

```bash
mkdir -p tools
cd tools
git clone --depth=1 git@github.com:andrearossini-bf/git-hooks-cordova.git
rm -rf tools/git-hooks-cordova/.git
cd ..
```

ATTENZIONE: Assicurarsi che `tools/` sia inserito nel `.gitignore` se si vuole tenere questo strumento fuori dalla repository del cliente!

Usare `rm -rf tools/git-hooks-cordova/.git` per non tracciare la repo di questo strumento.

### 3. Attivare gli hook

```bash
python tools/git-hooks-cordova/setup_hooks.py
```

A questo punto Git userà i file pre-commit / commit-msg contenuti in tools/git-hooks-cordova.

### 4. Lavorare normalmente

Ora ogni commit segue le regole definite:

- controllo versioni / changelog / branch name / commit message
- build Android / iOS (se necessario)
- blocco del commit in caso di errore

### 5. Disattivare gli hook (se serve)

```bash
python tools/git-hooks-cordova/disable_hooks.py
```

---

## 📂 Struttura

- git-hooks-cordova/
  - setup-hooks.py # script per attivare gli hook
  - disable-hooks.py # script per disattivare gli hook
  - pre-commit # wrapper pre-commit
  - commit-msg # wrapper commit-msg
  - .pre-commit-config.yaml # configurazione dei controlli
  - scripts/ # script di controllo / build
  - check_release_branch_versions.py
  - check_versions_consistency.py
  - build_android.py
  - build_ios.py

- I *wrapper* `pre-commit` / `commit-msg` fanno da ponte: lanciano i controlli definiti in `.pre-commit-config.yaml` e negli script quando si fanno commit, solo se gli hook sono attivati.  
- Gli script in `scripts/` contengono la logica di validazione versione, build, coerenza changelog/branch/commit-message, ecc.

---

## ✅ Cosa cambia (e cosa no) per il cliente

- La repo del cliente non contiene .pre-commit-config.yaml, né script, né configurazioni di build.
- Se il cliente non esegue i passi 2–3, non succede nulla: non interferisce.
- Se invece li esegui, hai un tool locale a supporto di release/build senza impatto sul repo remoto.

---

## 👷‍♂️ Policy / Convenzioni integrate

- Ogni rilascio (branch release/...) deve includere:
  - aggiornamento di versione in route.js e config.xml
  - entry nel CHANGELOG.md
  - commit name che include la versione
  - branch name che include la versione

- In caso di commit su branch non di release: route.js, config.xml, CHANGELOG.md non devono essere modificati.
- Se build Android / iOS fallisce → commit bloccato.

Questo sistema aiuta a mantenere coerenza e affidabilità sulla pipeline di rilascio.

---

## 🔧 Personalizzazione & Estensioni

- Puoi modificare gli script in scripts/ per adattarli ad altri flussi (ad esempio: aggiungere build web, test automatizzati, version bump semantico, versionCode, ecc.).
- Puoi aggiungere altri wrapper (es. pre-push) per ulteriori controlli.
- Tutto resta locale, e non impatta la repository del cliente.

---

## 📄 Licenza / Note

Questo repository è pensato per uso interno.
