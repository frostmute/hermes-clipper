# 🧪 The Capability Benchmark

Can we prove that usage = intelligence? **Yes.** 
Follow this test to see the "Agentic Flywheel" in action.

---

### Step 1: The "Blind" Baseline
1.  Choose a niche technical topic or a library released in the last 6 months (something the LLM wouldn't have in its base training data).
2.  Open a terminal and ask Hermes:
    `hermes chat -q "Explain how to use [Niche Topic X] for [Project Y]."`
3.  **The Result:** Hermes will likely give a generic answer or admit he doesn't have specific documentation.

### Step 2: The Contextual Feeding
1.  Find the documentation or a high-quality article for **[Niche Topic X]**.
2.  Use the **Hermes Clipper** browser extension to clip the page.
3.  Open Obsidian and click the **🧠 Brain Icon** to synthesize the note.
    *   *Watch as Hermes reads, cross-links, and moves the note to `Research/`.*

### Step 3: The "Enlightened" Query
1.  Ask Hermes the exact same question again:
    `hermes chat -q "Explain how to use [Niche Topic X] for [Project Y]."`
2.  **The Result:** Hermes will now find your synthesized note, pull the specific syntax/logic, and provide a perfectly cited, vault-aware response.

---

## 📈 Analysis
By using the clipper, you didn't just "save a link." You:
- **Expanded the Agent's RAG Surface:** He now has specialized "Search-First" data.
- **Improved Semantic Recall:** The synthesis step ensured the data was high-quality and project-linked.

**Conclusion:** Usage is not just storage. Usage is **Agent Training.** 🚀

---

## 📉 Efficiency Benchmark (v1.8.x)

With **Token Sovereignty 2.0**, we've shifted expensive reasoning from the LLM to local shell-based primitives.

### Comparison: Vault Discovery
| Method | Data Processed by LLM | Latency | Token Cost |
| :--- | :--- | :--- | :--- |
| **Agent `ls -R`** | ~50KB - 200KB (Text) | ~15s | High ($$$) |
| **Index-Driven** | ~1KB (Structural Index) | < 2s | Negligible (¢) |

### Comparison: Duplicate Handling
| Method | Process | Result |
| :--- | :--- | :--- |
| **Naive Agent** | Research → Extract → Write → "File already exists" | Session fully charged |
| **Grep Sieve** | Local grep check → "File exists, skipping" | **$0.00 (Zero Token Cost)** |

### Optimization Impact
- **Linguistic Compression (Caveman):** ~75% reduction in conversational overhead.
- **Head Extraction (4k char limit):** ~90% reduction in initial "read" tokens for large documentation pages.
- **Structural Indexing:** Eliminates the need for the Agent to "explore" the file system.
