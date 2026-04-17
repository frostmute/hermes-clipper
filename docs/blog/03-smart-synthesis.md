# Smart Synthesis: The Librarian in the Machine

### Genesis Part 3
*The prompt engineering behind autonomous note organization and vault-wide cross-linking.*

---

Why is it so hard to organize a vault? Because categorization is **High-Entropy Work**. Every new note requires you to hold your entire vault structure in your head to decide where it fits.

## The Librarian's Logic
In **Hermes Clipper**, the `synthesize` command is where the magic happens. We've programmed the Hermes Agent to act as an automated librarian. 

Instead of a simple "move file" command, the Agent follows a recursive logic:
1.  **Read:** Understand the core concepts of the new clip.
2.  **Recall:** Search the existing Obsidian vault for related topics.
3.  **Cross-Link:** Automatically add `[[Wikilinks]]` to the new note that point to existing project files.
4.  **Migrate:** Move the file from the "holding pen" (`Clippings/`) to a permanent folder (`Research/`, `Reference/`, etc.) based on the vault's established taxonomy.

## Prompting for Persistence
The "Secret Sauce" here is the instruction set. We don't just tell Hermes to "clean it up." We tell him to make it **"Vault-Ready."**

This includes:
- Updating YAML frontmatter with `status: permanent`.
- Adding a `Synthesized` tag.
- Identifying and fixing OCR or scraping errors.

By the time you open the note from the Obsidian Ribbon button, the work is already done. You don't "organize" your notes anymore—you just verify them.

---
*Next up: Caveman Tokens - Slashing LLM costs by 70% with linguistic compression.*
