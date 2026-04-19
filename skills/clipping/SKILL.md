---
name: clipping
description: Clip web content to Obsidian vault.
version: 0.1.0
license: MIT
---

# Web Clipper

Capture content, file in Obsidian. Use `hermes-clip`.

## Usage

### Clipping a URL
```bash
hermes-clip --url "URL" --title "TITLE" --content "MARKDOWN" --folder "SUBFOLDER" [--tags "TAGS"] [--mode "unique|merge|overwrite"]
```

### Synthesizing a Note
When asked to **Synthesize** a note:
1. **Read Note:** Read the content of the target `.md` file.
2. **Refine:**
   - Fix formatting, typos, and broken links.
   - Extract key themes and add relevant tags.
   - Identify cross-linking opportunities to other notes in the vault.
3. **Categorize:**
   - Use `VAULT_STRUCTURE.md` to find a permanent home (e.g. `Research/AI/Agents`).
   - If no suitable folder exists, create one or keep it in `Clippings/` if appropriate.
4. **Execute:**
   - Use `write_file` to save the refined content.
   - Use `mv` (shell) to move the file to its new destination if changed.
   - Report completion.

## Logic

1. **Extract:** 
... (rest of the file)

   - Read first 4k chars for categorization.
   - Extract full Markdown.
   - Identify topic, author, themes.

2. **Search Vault:**
   - Check `VAULT_STRUCTURE.md` index first.
   - Search notes (`grep -rl "source: [URL]"`).
   - If exists AND mode is `unique` → stop. Report path.
   - If exists AND mode is `merge` → Proceed to extract and append.
   - New topic → Set folder, use `mode="unique"`.

3. **Categorize:**
   - Logical folder tree (e.g. `Reference/Coding/React`).
   - Tags from content.

4. **Run:**
   - Call `hermes-clip`.
   - Report `path` + `uri`.

## Reasoning
"Clip React Hooks. Found 'React' folder, no 'Hooks' note. Create 'Reference/Coding/React/Hooks.md'. Tags #react #javascript."
