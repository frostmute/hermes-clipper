# The Bridge Pattern: Connecting Scouts to Local Brains

### Genesis Part 2
*Keeping our research local and our tools simple.*

---

The biggest challenge of building modern research tools isn't the scraping—it's the balance between **Capability and Security.** 

Browser extensions are intentionally sandboxed (and for good reason!). They shouldn't have access to your file system or run arbitrary scripts. But a research partner like the Hermes Agent needs access to your Obsidian vault to be truly helpful.

## The Solution: A Local Gateway
We solved this by implementing the **Bridge Pattern**. Instead of making a bloated, complex extension, we designed a simple "Scout." It identifies the content and sends it to a lightweight **FastAPI** server running locally on your own machine.

### How it Works:
1.  **The Scout (Extension):** Grabs the URL and raw content. Sends it to `localhost:8088`.
2.  **The Bridge (Server):** Ensures only *your* extension can talk to it via an API key.
3.  **The Hand (CLI):** Handles the "grunt work" of saving files and organizing folders.
4.  **The Brain (Agent):** Dispatched only when you need deep research or synthesis.

## Smooth and Async
Agentic research can take time—sometimes over a minute for a deep-dive. A browser extension will timeout long before that.

We built an **Async Task Tracker**. When you click "Agent Research," the bridge starts the task and gives the extension a `task_id`. This keeps the UI responsive (with our "Pulse" status) without hanging your browser or losing the connection.

## Sovereignty by Design
By decoupling the browser from the vault, we've kept your data local and secure. This architecture means your research stays on your machine, where it belongs, while still benefiting from modern AI orchestration.

---
*Next up: Smart Synthesis - Teaching our librarian to organize for us.*
