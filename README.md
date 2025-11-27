# git-hooks-cordova — Hook Git personalizzati per Cordova

Questo repository contiene un set di *git hooks* personalizzati e automatismi pensati per gestire release e build del progetto (version bump, build Android/iOS, controlli di coerenza, ecc.), senza sporcare il repository principale del cliente.

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

## 🎯 Obiettivo

Permettere di:

- **gestire versioning, changelog e build in modo sicuro** (Android / iOS),  
- **garantire coerenza** tra versione su codice, config, branch, changelog e commit message,  
- far sì che la **repo del cliente rimanga pulita** — nessun file di configurazione commit-ato, nessuno script di build —  
- avere un sistema **facile da attivare e disattivare** in locale.

---

## 🚀 Uso (per sviluppatore / te)

### 1. Clonare il repo del cliente

```bash
git clone <repo-cliente>
cd <repo-cliente>
```

### 2. Scaricare i hook

```bash
mkdir -p tools
cd tools
git clone git@github.com:andrearossini-bf/git-hooks-cordova.git
cd ..
```

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

## ✅ Cosa cambia (e cosa no) per il cliente

- La repo del cliente non contiene .pre-commit-config.yaml, né script, né configurazioni di build.
- Se il cliente non esegue i passi 2–3, non succede nulla: non interferisce.
- Se invece li esegui, hai un tool locale a supporto di release/build senza impatto sul repo remoto.

## 👷‍♂️ Policy / Convenzioni integrate

- Ogni rilascio (branch release/...) deve includere:
  - aggiornamento di versione in route.js e config.xml
  - entry nel CHANGELOG.md
  - commit name che include la versione
  - branch name che include la versione

- In caso di commit su branch non di release: route.js, config.xml, CHANGELOG.md non devono essere modificati.
- Se build Android / iOS fallisce → commit bloccato.

Questo sistema aiuta a mantenere coerenza e affidabilità sulla pipeline di rilascio.

## 🔧 Personalizzazione & Estensioni

- Puoi modificare gli script in scripts/ per adattarli ad altri flussi (ad esempio: aggiungere build web, test automatizzati, version bump semantico, versionCode, ecc.).
- Puoi aggiungere altri wrapper (es. pre-push) per ulteriori controlli.
- Tutto resta locale, e non impatta la repository del cliente.

## 📄 Licenza / Note

Questo repository è pensato per uso interno.
