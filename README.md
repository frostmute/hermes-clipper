# ⚡ Hermes Clipper

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Obsidian](https://img.shields.io/badge/Obsidian-v0.15.0%2B-7C4DFF)](https://obsidian.md/)
[![Hermes Agent](https://img.shields.io/badge/Agent-Hermes-D4AF37)](https://github.com/frostmute/hermes-agent)

> **"Too lazy to file it yourself? I got you."**
> An intelligent, agent-driven web clipping ecosystem that leverages the Hermes Agent to autonomously organize, research, and refine your knowledge directly into your Obsidian vault.

---

## 🌟 Overview

**Hermes Clipper** is not just another bookmarking tool. It's a decentralized suite designed to turn the friction of web-clipping into a **Contextual Nutrient System** for your AI Agent. Instead of hoarding links in a digital graveyard, Hermes Clipper feeds your research directly to your "Second Brain," allowing the **Hermes Agent** to categorize, cross-link, and synthesize your knowledge in real-time.

### Why Hermes Clipper?
- **Zero Friction:** One-click from your browser, handled by an agent.
- **Agent-First:** Stop picking folders. Let Hermes decide where it belongs based on your vault's existing context.
- **Token Sovereignty 2.0:** Deeply optimized for LLM efficiency.
    - **Smart Duplicate Detection:** Local `grep` sieve prevents redundant Agent research.
    - **Vault Structural Index:** Auto-generated folder map eliminates expensive recursive listings.
    - **Linguistic Compression:** Built-in **Caveman Mode** support to slash LLM costs by ~75%.
- **Local Sovereignty:** Your data stays in your vault. Secure bridge with API key protection.

---

## 📖 Documentation

Explore the technical depth of the Hermes Clipper ecosystem:

- **[Architecture](docs/architecture.md):** Deep-dive into the Bridge Pattern and Agentic Ingestion.
- **[The Secret Sauce](docs/THE_SAUCE.md):** How we achieve 75%+ token efficiency.
- **[Benchmark](docs/BENCHMARK.md):** Empirical tests of Agent speed and accuracy.
- **[Community & Inspirations](docs/COMMUNITY.md):** The giants we stand on.
- **[Migration Guide](docs/MIGRATION.md):** Transitioning from Raindrop.io or Readwise.

---

## 🛠 The Suite

Hermes Clipper is composed of five modular components:

1.  **🧠 The Brain (Skill):** Optimized procedural logic for Hermes Agent. Now features **Head Extraction** (~4k chars) for categorization efficiency.
2.  **📡 The Bridge (FastAPI):** A secure local gateway connecting browsers and plugins to the Agent.
3.  **🛰️ The Scout (Extension):** A sleek Chrome/Firefox extension for 1-click capture.
4.  **🔨 The Hand (CLI):** A powerful standalone tool featuring a smart setup wizard that auto-provisions your Agent's memory.
5.  **🏡 The Garden (Plugin):** An Obsidian ribbon interface for synthesis and status monitoring.

---

## 🚀 Getting Started

### Prerequisites
- [Hermes Agent](https://github.com/frostmute/hermes-agent) installed and configured.
- Python 3.8+
- [Obsidian](https://obsidian.md/)

### Installation

1. **Bootstrap local env:**
   ```bash
   git clone https://github.com/frostmute/hermes-clipper.git
   cd hermes-clipper
   ./scripts/bootstrap.sh
   ```
   This creates `.venv`, installs editable, and links `hermes-clip` into `~/.local/bin/`.

2. **Run Setup:**
   ```bash
   hermes-clip setup
   ```
   *Note: This generates your API Key, deploys the optimized Skill to Hermes, and builds your Vault Structural Index.*

3. **Start the Bridge:**
   ```bash
   hermes-clip serve --daemon
   ```
   *Note: Use `hermes-clip status` to verify and `hermes-clip stop` to shut it down.*

4. **Install Browser Extension:**
   - Open Chrome/Firefox Extensions page.
   - Enable "Developer Mode".
   - "Load unpacked" and select the `extension/` folder in this repo.
   - **Configuration:** Open the extension popup, right-click and select "Inspect", then run this in the console to save your API Key:
     ```javascript
     localStorage.setItem('hermes_api_key', 'YOUR_API_KEY_HERE');
     ```

4. **Install Obsidian Plugin:**
   - Copy `obsidian-plugin/` contents to `<vault>/.obsidian/plugins/hermes-clipper/`.
   - Enable in Obsidian settings and enter your API Key.

---

## 📖 Usage

### Quick Clip
Click the **⚡ Hermes** icon in your browser to send the current page to your `Clippings/` folder.

### Agent Research
Click **Agent Research** in the extension. Hermes will research the topic, check your vault for context, and file it intelligently.

### Synthesis (Obsidian)
Click the **🧠 Brain** icon in your Obsidian ribbon. Hermes will:
1. Read the note.
2. Fix formatting & typos.
3. Cross-link to other notes.
4. Move it from `Clippings/` to a permanent home (e.g., `Research/`).

---

## 🛡 Security

Hermes Clipper uses a local-first bridge with:
- **X-API-Key Header:** All requests to the bridge require your unique key.
- **CORS Restricted:** Only listens to your browser extension and Obsidian app.
- **Privacy:** No cloud storage. No data leaks.

---

## 🌑 Philosophy: Agent-Growth

Every clip you save expands your Agent's context. By integrating clipping into your inherent workflow, you are building a sharper, more integrated AI that understands your research interests better with every note.

---

## ☕ Support

If Hermes Clipper has saved you a mountain of tokens or made your vault a better place, consider throwing some dollarbucks my way!

[**Support on Ko-fi**](https://ko-fi.com/frostmute)

---

## 📜 Credits & License

- **Caveman Mode:** Methodology by [Julius Brussee](https://github.com/JuliusBrussee/caveman).
- **Hermes Agent:** The foundational intelligence ecosystem.

Licensed under the [MIT License](LICENSE).

---
*⚡ Build a better garden. Grunt.*
