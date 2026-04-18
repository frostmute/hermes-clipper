# Hermes Clipper: Development Log & Technical Spec

## 📝 Overview
**Hermes Clipper** is an intelligent, agent-driven web clipping solution that integrates the **Hermes Agent** with **Obsidian**. Unlike traditional clippers, it offloads categorization, summarization, and metadata management to an LLM-native agent.

## 🚀 Architecture

Hermes Clipper is built on a modular, agent-first architecture:

### Core Components
- **`hermes-clip` CLI Tool:**
    - **Location:** `src/hermes_clipper/main.py` (Installed via `./scripts/bootstrap.sh`)
    - **Features:** Setup wizard, custom templates, direct URL extraction (requests/bs4), conflict resolution (unique/merge/overwrite), and JSON output with Obsidian URIs.
- **`clipping` Skill:**
    - **Location:** `skills/clipping/`
    - **Function:** Logic for Hermes to research, search the vault for context, and intelligently file new clippings.
- **Bridge Server:**
    - **Implementation:** FastAPI server running on `localhost:8088`.
    - **Lifecycle Management:** Managed as a persistent CLI daemon (`hermes-clip serve --daemon`).
    - **Endpoints:**
        - `POST /clip`: Direct clipping of provided content.
        - `POST /agent/clip`: Dispatches a background Hermes Agent for autonomous research and clipping ("Agent-Mode").
        - `GET /status`: Health check for the bridge.

### Token Optimization Layer
- **Vault Indexing:** Setup generates `~/.hermes/memories/VAULT_STRUCTURE.md`. Agent reads this ~1KB file instead of running `ls -R` (potentially ~100KB+ output).
- **Grep Sieve:** `check_duplicate()` uses local `grep` to find existing source URLs. Agent is only dispatched if the URL is unique.
- **Head Extraction:** The `clipping` skill is tuned to read the first 4,000 characters for classification, minimizing initial context window usage.

### Source Control
- **GitHub:** Public repository at `frostmute/hermes-clipper`.
- **Structure:** Clean Python package structure ready for public distribution.
