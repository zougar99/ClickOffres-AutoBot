# 💡 ClickOffres-AutoBot — Automated desktop app for QA/legal testing of web forms with proxy rotation, multi-device simulation, and AI-powered field mapping

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/zougar99/ClickOffres-AutoBot/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/zougar99/ClickOffres-AutoBot?style=social)](https://github.com/zougar99/ClickOffres-AutoBot)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue)](https://github.com/zougar99/ClickOffres-AutoBot)

> Automated desktop app for QA/legal testing of web forms with proxy rotation, multi-device simulation, and AI-powered field mapping.

---

## 📖 Table of Contents
- [Features](#-features)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Screenshots](#-screenshots)
- [Roadmap](#-roadmap)
- [FAQ](#-faq)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features
- ✔ **Auto Form Filling** — AI maps and fills web forms automatically
- ✔ **Proxy Rotation** — Built-in proxy manager with auto-rotation per session
- ✔ **Multi-Device** — Simulates desktop, mobile, and tablet user agents
- ✔ **QA Testing** — Captures screenshots and logs for each test run
- ✔ **Batch Mode** — Process thousands of URLs from a CSV file
- ✔ **AI Field Mapping** — ML model auto-detects field types and fills appropriately
- ✔ **Report Export** — HTML/PDF/CSV test reports with screenshots

---

## 🔮 How It Works

```
  Input ──► Processing Pipeline ──► Output
  ┌────────┐   ┌────────┐   ┌────────┐
  │ Data   │──►│ Engine │──►│ Result │
  │ Source │   │ Logic  │   │        │
  └────────┘   └────────┘   └────────┘
```

1. **Input** — Load data from file, API, or user input
2. **Process** — Core engine applies logic/analysis/transformation
3. **Output** — Results displayed in UI, saved to file, or sent via API

---

## 💻 Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| UI | CustomTkinter |
| Browser | Selenium + Playwright |
| AI | OpenAI / local LLM |
| Storage | SQLite |

---

## 🚀 Installation

```bash
git clone https://github.com/zougar99/ClickOffres-AutoBot.git
cd ClickOffres-AutoBot
pip install -r requirements.txt
playwright install chromium
```

---

## 📄 Configuration

Create a `config.yaml` or `.env` file in the project root:

```yaml
# Application settings
debug: false
port: 8080
theme: dark
language: en
```

---

## 🧰 Usage Guide

1. Launch: `python main.py`
2. Upload a CSV of target URLs
3. Select profile (desktop/mobile/tablet)
4. Click **Start** to begin automated testing
5. Review results in the Reports tab

---

## 🖼 Screenshots

> *(Screenshots coming soon. PRs welcome!)*

---

## 🔄 Roadmap

- 🟢 Web dashboard
- 🟡 Mobile companion app
- ⚫ API access
- ⚫ Plugin system
- ⚫ Multi-language support

---

## ❓ FAQ

### Is this for web scraping?
No — it's for QA/legal testing of web forms, not data extraction.

### How many proxies do I need?
At least 5-10 for smooth rotation; the tool supports HTTP/HTTPS/SOCKS5 proxies.

---

## 🚧 Troubleshooting

| Problem | Solution |
|---------|----------|
| **App won't start** | Check Python version (3.10+); run `pip install -r requirements.txt` |
| **No output** | Check logs in `logs/` folder; enable debug mode in config |
| **Performance issues** | Close other applications; reduce batch size in config |
| **Dependency errors** | Create fresh venv: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📐 License
Distributed under the **MIT License**. See [`LICENSE`](https://github.com/zougar99/ClickOffres-AutoBot/blob/main/LICENSE) for more information.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/zougar99">zougar99</a>
</p>
