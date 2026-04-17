# Hermes Clipper: Development Log & Technical Spec

## 📝 Overview
**Hermes Clipper** is an intelligent, agent-driven web clipping solution that integrates the **Hermes Agent** with **Obsidian**. Unlike traditional clippers, it offloads categorization, summarization, and metadata management to an LLM-native agent.

## 🚀 Progress & Current State

### 1. Environment Configuration
- **Vault Integration:** Established `~/Documents/ObsidianVault` as the primary Obsidian vault.
- **Hermes Setup:** Configured `OBSIDIAN_VAULT_PATH` in `.hermes/.env` to allow agent-level access to the vault.
- **Local Config:** Created `~/.config/hermes-clipper/` for persistent settings and custom templates.

### 2. Core Components Built
- **`hermes-clip` CLI Tool (Advanced):**
    - **Location:** `src/hermes_clipper/main.py` (Installed via `pip -e .`)
    - **Features:** Setup wizard, custom templates, direct URL extraction (requests/bs4), conflict resolution (unique/merge/overwrite), and JSON output with Obsidian URIs.
- **`clipping` Skill:**
    - **Location:** `skills/clipping/`
    - **Function:** Logic for Hermes to research, search the vault for context, and intelligently file new clippings.
- **Bridge Server (Phase 2):**
    - **Implementation:** FastAPI server running on `localhost:8088`.
    - **Endpoints:**
        - `POST /clip`: Direct clipping of provided content.
        - `POST /agent/clip`: Dispatches a background Hermes Agent for autonomous research and clipping ("Agent-Mode").

### 4. Token Optimization Layer (Phase 2.5)
- **Vault Indexing:** Setup generates `~/.hermes/memories/VAULT_STRUCTURE.md`. Agent reads this ~1KB file instead of running `ls -R` (potentially ~100KB+ output).
- **Grep Sieve:** `check_duplicate()` uses local `grep` to find existing source URLs. Agent is only dispatched if the URL is unique.
- **Head Extraction:** The `clipping` skill is tuned to read the first 4,000 characters for classification, minimizing initial context window usage.

### 5. Source Control
- **GitHub:** Private repository initialized at `frostmute/hermes-clipper`.
- **Structure:** Clean Python package structure ready for public distribution.

---

## 🛠 Architecture for Public Release

### Phase 1: Local CLI & Skill (Complete)
- Standalone CLI tool and Hermes-compatible skill.

### Phase 2: The "Bridge" (Complete)
- FastAPI server bridging external triggers to the Hermes Agent.
- Added **Agent-Mode** for autonomous multi-turn research tasks.
- **Integrated Optimizations:** Local duplicate checks and structural indexing.

### Phase 3: Browser Extension (Next Step)
- **Function:** A "One-Click" button in Chrome/Firefox.
- **Logic:** Extracts the page Markdown and sends it to the Local Bridge.
- **Integration:** Will support both "Quick Clip" and "Agent Research" modes.

---

## 📅 Roadmap to Public Release

1.  **Refine Agent Prompts:** Fine-tune the "research" prompt for better autonomous organization.
2.  **Formalize the Skill:** Submit to the **Hermes Skills Hub**.
3.  **Bridge Improvements:** Add background task queue for long-running agent tasks.
4.  **Extension Development:** Build and publish the browser extension.

## 💡 Design Philosophy
- **Agent-First:** Hermes knows where your data belongs better than you do.
- **Zero-Config:** One-click from the browser, agent handles the rest.
- **Obsidian Native:** Deep integration with vault structures and Wikilinks.
