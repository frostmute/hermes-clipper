# GEMINI.md

This file contains foundational mandates, project-specific instructions, and conventions for Gemini CLI. These instructions take absolute precedence over general workflows.

## 🎯 Project Overview
- **Goal:** Raindrop.io Integration for Obsidian ("Make It Rain"). Seamlessly import bookmarks, highlights, and notes from Raindrop.io into Obsidian vaults.
- **Status:** Active Development (v1.8.0).

## 🛠 Tech Stack
- **Language:** TypeScript (v5.3.3)
- **Framework:** Obsidian Plugin API
- **Tooling:** Esbuild (bundling), Jest (testing), Handlebars (templating)
- **Environment:** Electron (Obsidian host)

## 📜 Coding Standards & Conventions
- **Architecture:** Modular architecture. Core logic in `src/main.ts`, with reusable logic in `src/utils/`.
- **Patterns:** Functional programming patterns preferred (pure functions, immutable data).
- **Naming:** 
    - `PascalCase` for classes and types.
    - `camelCase` for functions, variables, and properties.
    - `SCREAMING_SNAKE_CASE` for constants and enums.
- **Style:** Strict TypeScript. `noImplicitAny` and `strictNullChecks` are enabled. Avoid `any` at all costs.
- **Documentation:** Use JSDoc for public functions and complex logic.
- **Linter/Formatter:** Markdown files must pass `markdownlint`.

## 🧪 Testing Strategy
- **Framework:** Jest with `ts-jest` and `jest-environment-jsdom`.
- **Command:** `npm test`
- **Coverage:** Use `npm run test:coverage` to verify impact.
- **Requirement:** All bug fixes and new features must be accompanied by relevant test cases in the `tests/` directory.

## 🚀 Workflows & Mandates
- **Validation:** Always run `npm run build` to verify both TypeScript compilation (`tsc`) and bundling (`esbuild`).
- **Surgical Updates:** `main.ts` is large (2800+ lines); perform surgical edits to avoid breaking unrelated functionality.
- **Security:** Never log or commit Raindrop API tokens. Protect user vault paths and metadata.
- **Releases:** Version bumps require running `node scripts/version-bump.mjs`.

## 🤖 Hermes Agent Integration
The `hermes-agent` is installed locally and should be utilized for tasks beyond the immediate scope of standard CLI tools.

- **Capabilities:**
    - **Browser Automation:** Use for deep web research, scraping, or interacting with web UIs via `hermes tool call browser`.
    - **Advanced Reasoning:** Delegate complex, multi-step research or planning tasks using `hermes`.
    - **Skill Acquisition:** Utilize and create skills for recurring workflows (`hermes skills`).
    - **Background Tasks:** Offload long-running background processes or automations via `hermes cron`.
- **Interaction:**
    - Invoke directly via the `hermes` command.
    - Check health and configuration with `hermes doctor`.
    - View active sessions and memory with `hermes session_search` and by checking `.hermes/memories/`.
- **Workflow Mandate:** 
    - For tasks requiring live web interaction, external toolsets not available here, or persistent multi-turn research, delegate to **Hermes**.
    - Sync relevant findings from Hermes back into this workspace's documentation.

## ⚠️ Known Issues & Technical Debt
- **Large Main File:** `src/main.ts` is becoming monolithic and may eventually require further decomposition into smaller components.
- **Rate Limiting:** Ensure the `RateLimiter` utility is used for all Raindrop API interactions to avoid 429 errors.

---
*Note: This file is a living document. Update it as project requirements and conventions evolve.*
