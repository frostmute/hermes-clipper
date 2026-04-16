---
name: clipping
description: Intelligently clip web content into the Obsidian vault.
---

# Web Clipper

This skill allows Hermes to capture web content and file it into the Obsidian vault. It leverages the `hermes-clip` CLI tool for advanced metadata and organization.

## Usage

```bash
hermes-clip --url "URL" --title "TITLE" --content "MARKDOWN" --folder "SUBFOLDER" [--tags "TAGS"] [--mode "unique|merge|overwrite"]
```

## Logic (The "Intelligent" Workflow)

1. **Research & Extract:** 
   - Use browser tools to navigate to the target URL.
   - Extract the full content in Markdown.
   - Identify the primary topic, author, and key themes.

2. **Contextual Search (CRITICAL):**
   - **Search the Vault First:** Use `ls` or `grep` (via `terminal` tool) to see if you already have notes on this topic or from this source.
   - **Decide Action:**
     - If it's a new topic: Use `mode="unique"` and a new `folder`.
     - If it's an update to existing research: Use `mode="merge"` or `mode="overwrite"`.

3. **Categorization:**
   - Choose a logical folder hierarchy (e.g., `Reference/Coding/React`, `Research/Personal/Finance`).
   - Generate relevant tags based on the content.

4. **Execution:**
   - Call `hermes-clip` with the gathered data.
   - **Report Success:** Provide the user with the `path` and the `uri` returned in the JSON output so they can open the note.

## Example Reasoning
"The user wants to clip a React Hooks tutorial. I searched the vault and found an existing 'React' folder but no 'Hooks' note. I will create 'Reference/Coding/React' and file it as 'Hooks.md' with tags #react #javascript."
