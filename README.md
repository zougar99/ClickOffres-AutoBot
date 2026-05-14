# 🤖 ClickOffres AutoBot

> **Automated desktop application for QA/legal testing of web forms.**  
> *Usage: legal QA/testing only — no spoofing, no bypass, no fake traffic.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-2563eb?style=flat&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat)]()
[![Telegram](https://img.shields.io/badge/Telegram-werlist99-3b82f6?style=flat&logo=telegram)](https://t.me/werlist99)

---

## 📦 Installation

### 1️⃣ Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Install Playwright browser
```bash
playwright install chromium
```

---

## 🚀 Usage

```bash
python app.py
```

### 🧭 Dashboard Navigation

| Panel | Description |
|-------|-------------|
| 📋 **General** | Profile name, user data fields, cookies editor |
| 🌐 **Proxy Center** | Runtime proxy, proxy list, checker, saved working proxies, best proxy, CSV export |
| ⚙️ **Platform** | Device profile + fill mode + analyze/preview/fill/submit + field mapping |
| 🔐 **Session** | Open login session, save/load session snapshot, pull/apply cookies |
| 📊 **Reports** | Run history and JSON export |
| 📝 **Logs** | Runtime log stream |

### ⚡ Quick Workflow

1. 📝 Fill in the data in **General**
2. 🌐 (Optional) Configure/check proxies in **Proxy Center**
3. 💾 Save profile/template to **Profile Studio**
4. 🔗 Enter target URL then **Analyze**
5. ✅ Check mapping, launch **Preview** → **Fill Form**
6. 📬 **Submit** if necessary

---

## ✨ Key Features

- 🎯 **AdsPower-like layout** — sidebar + modular panels
- 📱 **Device profiles** — Windows, macOS, Android, iOS, Linux
- 🔀 **Fill modes** — `random` / `sequential`
- 🛡️ **Proxy Center** — list management, auto-checker (OK/FAIL, IP, latency), best proxy auto-apply, CSV export
- 🧑‍💻 **Profile Studio** — save/load/delete profiles, import/export JSON, template presets
- 👁️ **Preview mode** — before actual filling
- 🔑 **Login session** — optional session before Analyze
- 🤖 **Smart Run** — multi-device automated run with proxy rotation
- 🧠 **AI Auto Map** — intelligent field matching
- 🎲 **Fake Data Generator** — bulk profile generation with country presets

---

## 📂 Supported Fields

| Category | Fields |
|----------|--------|
| 👤 Identity | First name, Last name, Full name, Gender, Date of birth |
| 📧 Contact | Email, Phone, Address, City, Zip code, Country |
| 💼 Professional | Company, Job title, Website, LinkedIn |
| 📄 Documents | Message/Cover letter, CV upload |
| 🔐 Account | Username, Password |

---

## 🔧 Build .exe (Windows)

```batch
build_release.bat
```

The binary will be generated in `dist/ClickOffresAutoBot.exe`.

---

## 📁 Persistence Files

| File | Description |
|------|-------------|
| `user_data.json` | User data |
| `proxy_config.json` | Current runtime proxy |
| `proxy_list.json` | Proxy list + saved working proxies |
| `profiles.json` | Complete profiles |
| `templates.json` | Templates Profile Studio |
| `sessions/*.json` | Session snapshots (storage state) |
| `run_history.json` | Run reports history |

---

## 🧑‍💻 Contact

**Telegram: [werlist99](https://t.me/werlist99)**

---

> ⚠️ **Legal Notice** — This tool is intended for legitimate QA testing only.  
> Unauthorized use for bypassing security, scraping without consent, or any illegal activity is strictly prohibited.
