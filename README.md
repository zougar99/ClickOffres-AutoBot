# ClickOffres AutoBot

Application desktop automatisée pour QA/testing legal de formulaires web.
Usage: legal QA/testing uniquement (pas de spoofing, pas de bypass, pas de fake traffic).

## Installation

### 1. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 2. Installer le navigateur Playwright

```bash
playwright install chromium
```

## Utilisation

### Lancer l'application

```bash
python app.py
```

### Dashboard navigation

- `General`: profile name/group/tags/remark, user data fields, cookies editor
- `Proxy Center`: runtime proxy, proxy list, checker, saved working proxies, best proxy, CSV export
- `Platform`: device profile + fill mode + analyze/preview/fill/submit + field mapping
- `Session`: open login session, save/load session snapshot, pull/apply cookies
- `Reports`: run history and JSON export
- `Logs`: runtime log stream

### Workflow rapide

1. Remplir les données dans `Dashboard`
2. (Optionnel) Configurer/checker proxies dans `Proxy Center`
3. Sauvegarder profile/template dans `Profile Studio`
4. Entrer URL cible puis `Analyze`
5. Vérifier mapping, lancer `Preview` puis `Fill Form`
6. `Submit` si nécessaire

### Key features

- AdsPower-like layout avec sidebar et panels modulaires
- Device profiles standards: Windows / macOS / Android / iOS
- Fill mode: `random` / `sequential`
- Proxy Center avec:
  - list management (formats multiples)
  - checker automatique (OK/FAIL, IP, latence)
  - best proxy auto-apply
  - export CSV des résultats
- Profile Studio avec:
  - save/load/delete profiles
  - import/export JSON
  - template presets + save current as template
- Preview mode avant remplissage réel
- Login session optionnelle avant Analyze

### Build .exe (Windows)

```bat
build_release.bat
```

Le binaire sera généré dans `dist/ClickOffresAutoBot.exe`.

### Champs supportés

- Prénom / Nom / Nom complet
- Email
- Téléphone
- Adresse / Ville / Code postal / Pays
- Entreprise / Poste
- Site web / LinkedIn
- Message / Lettre de motivation
- CV (upload de fichier)
- Username / Password
- Date de naissance / Genre

### Persistence files

- `user_data.json`: données utilisateur
- `proxy_config.json`: runtime proxy actuel
- `proxy_list.json`: proxy list + saved working proxies
- `profiles.json`: profils complets
- `templates.json`: templates Profile Studio
- `sessions/*.json`: session snapshots (storage state)
- `run_history.json`: run reports history
