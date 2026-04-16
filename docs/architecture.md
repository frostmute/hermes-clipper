# Hermes Clipper: Development Log & Technical Spec

## 📝 Overview
**Hermes Clipper** is an intelligent, agent-driven web clipping solution that integrates the **Hermes Agent** with **Obsidian**. Unlike traditional clippers, it offloads categorization, summarization, and metadata management to an LLM-native agent.

## 🚀 Progress & Current State

### 1. Environment Configuration
- **Vault Integration:** Established `/home/frost/Endeavor` as the primary Obsidian vault.
- **Hermes Setup:** Configured `OBSIDIAN_VAULT_PATH` in `.hermes/.env` to allow agent-level access to the vault.

### 2. Core Components Built
- **`hermes-clip` CLI Tool:**
    - **Location:** `~/.local/bin/hermes-clip`
    - **Function:** Handles YAML frontmatter generation, filename sanitization, duplicate prevention, and folder creation.
    - **Language:** Python 3.
- **`clipping` Skill:**
    - **Location:** `.hermes/hermes-agent/skills/note-taking/clipping/`
    - **Function:** Provides Hermes with the procedural logic to browse, extract content, determine appropriate categorization (sub-folders), and execute the clip.

### 3. Verified Workflow
- **Test Case:** "Clip the Obsidian Plugin API documentation."
- **Outcome:** Hermes autonomously searched, extracted the `Plugin` class documentation, and filed it under `Reference/Obsidian/` in the vault with correct metadata.

---

## 🛠 Architecture for Public Release

### Phase 1: Local CLI & Skill (Complete)
- Standalone CLI tool and Hermes-compatible skill.
- Requirement: User manually sets `OBSIDIAN_VAULT_PATH`.

### Phase 2: The "Bridge" (Next Step)
- **Goal:** Allow external triggers (like a browser extension) to talk to the local Hermes instance.
- **Implementation:** A lightweight local server (FastAPI or Node.js) listening on a local port (e.g., `localhost:8088`).
- **Endpoint:** `POST /clip` accepting `{ url, title, content }`.
- **Action:** The bridge executes `hermes chat -q "..." -s clipping` or calls the `clipping` skill directly via RPC.

### Phase 3: Browser Extension
- **Function:** A "One-Click" button in Chrome/Firefox.
- **Logic:** Extracts the page Markdown (using a library like `Turndown`) and sends it to the Local Bridge.
- **Key Differentiator:** The extension doesn't need complex settings; it just sends data to Hermes, who decides where it goes.

---

## 📅 Roadmap to Public Release

1.  **Package the CLI:** Create a `pip` installable package for `hermes-clip`.
2.  **Formalize the Skill:** Submit the `clipping` skill to the **Hermes Skills Hub**.
3.  **Bridge Server:** Develop a single-command bridge (e.g., `hermes-clip server`).
4.  **Extension Store:** Develop and publish the browser extension.

## 💡 Design Philosophy
- **Agent-First:** The user should never have to pick a folder. Hermes should know where it belongs based on their existing vault structure and `MEMORY.md`.
- **Zero-Config (Extension):** The browser extension should only require the "Bridge URL" (defaulting to localhost).
- **Privacy:** All processing happens locally or via the user's configured LLM provider in Hermes.
