#!/usr/bin/env /usr/bin/python3
import os
import sys
import datetime
import argparse
import re
import json
import subprocess
from pathlib import Path

# Try to import extraction libraries for direct mode
try:
    from bs4 import BeautifulSoup
    import requests
    HAS_EXTRACTION = True
except ImportError:
    HAS_EXTRACTION = False

CONFIG_DIR = Path.home() / ".config" / "hermes-clipper"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_TEMPLATE = """---
title: "{{title}}"
source: {{url}}
clipped: {{date}}
tags: [{{tags}}]
status: unread
---

# {{title}}

{{content}}
"""

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def setup_wizard():
    print("Welcome to the Hermes Clipper Setup Wizard!")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = load_config()
    
    current_vault = config.get("vault_path") or os.environ.get("OBSIDIAN_VAULT_PATH", "")
    vault_path = input(f"Enter your Obsidian Vault path [{current_vault}]: ").strip() or current_vault
    
    if not vault_path:
        print("Error: Vault path is required.")
        return

    vault_path = os.path.expanduser(vault_path)
    if not os.path.exists(vault_path):
        print(f"Warning: Path {vault_path} does not exist. Creating it...")
        os.makedirs(vault_path, exist_ok=True)
    
    config["vault_path"] = vault_path
    
    # Template setup
    template_path = CONFIG_DIR / "template.md"
    if not template_path.exists():
        with open(template_path, "w") as f:
            f.write(DEFAULT_TEMPLATE)
        print(f"Created default template at {template_path}")
    
    config["template_path"] = str(template_path)
    save_config(config)
    
    print("\nSetup Complete!")
    print(f"Vault: {vault_path}")
    print(f"Template: {template_path}")
    print("\nTip: Add 'export OBSIDIAN_VAULT_PATH=\"{}\"' to your .bashrc for Hermes Agent integration.".format(vault_path))

def extract_content(url):
    if not HAS_EXTRACTION:
        print("Error: 'requests' and 'beautifulsoup4' are required for direct extraction.")
        print("Install them with: pip install requests beautifulsoup4")
        sys.exit(1)
    
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Simple extraction logic: find title and main text
        title = soup.title.string if soup.title else "Untitled"
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        content = soup.get_text(separator="\n", strip=True)
        return title, content
    except Exception as e:
        print(f"Direct extraction failed: {e}")
        sys.exit(1)

def sanitize_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title).strip()

def clip(url, title, content, folder="Clippings", tags=None, metadata=None, mode="unique"):
    config = load_config()
    vault = config.get("vault_path") or os.environ.get("OBSIDIAN_VAULT_PATH")
    
    if not vault:
        print("Error: Vault path not set. Run 'hermes-clip setup' first.")
        sys.exit(1)
        
    filename = sanitize_filename(title)
    if not filename:
        filename = "Untitled_Clipping_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
    target_dir = os.path.normpath(os.path.join(vault, folder))
    os.makedirs(target_dir, exist_ok=True)
    
    path = os.path.join(target_dir, f"{filename}.md")
    
    # Conflict Resolution
    if os.path.exists(path) and mode == "unique":
        counter = 1
        while os.path.exists(path):
            path = os.path.join(target_dir, f"{filename}_{counter}.md")
            counter += 1
    elif os.path.exists(path) and mode == "merge":
        with open(path, "a") as f:
            f.write(f"\n\n--- \n*Appended on {datetime.datetime.now()}*\n\n{content}")
        return path

    # Load Template
    template_path = config.get("template_path")
    template = DEFAULT_TEMPLATE
    if template_path and os.path.exists(template_path):
        with open(template_path, "r") as f:
            template = f.read()

    # Process tags
    tag_list = ["clipping"]
    if tags:
        tag_list.extend([t.strip() for t in tags.strip("[]").split(",")])
    tag_str = ", ".join(list(set(tag_list)))

    # Render Template
    rendered = template.replace("{{title}}", title)\
                       .replace("{{url}}", url)\
                       .replace("{{content}}", content)\
                       .replace("{{date}}", str(datetime.date.today()))\
                       .replace("{{tags}}", tag_str)

    # Handle extra metadata
    if metadata:
        try:
            extra_meta = json.loads(metadata)
            meta_str = "\n".join([f"{k}: {v}" for k, v in extra_meta.items()])
            rendered = rendered.replace("---", f"---\n{meta_str}", 1)
        except:
            pass

    with open(path, "w") as f:
        f.write(rendered)
    
    # Output result
    vault_name = os.path.basename(vault)
    relative_path = os.path.relpath(path, vault)
    print(json.dumps({
        "status": "success",
        "path": path,
        "uri": f"obsidian://open?vault={vault_name}&file={relative_path}"
    }))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hermes Clipper for Obsidian")
    subparsers = parser.add_subparsers(dest="command")

    # Setup command
    subparsers.add_parser("setup", help="Run the configuration wizard")

    # Clip command
    clip_parser = subparsers.add_parser("clip", help="Clip content to Obsidian")
    clip_parser.add_argument("--url", required=True)
    clip_parser.add_argument("--title")
    clip_parser.add_argument("--content")
    clip_parser.add_argument("--folder", default="Clippings")
    clip_parser.add_argument("--tags")
    clip_parser.add_argument("--metadata")
    clip_parser.add_argument("--mode", choices=["unique", "merge", "overwrite"], default="unique")
    clip_parser.add_argument("--direct", action="store_true", help="Extract content directly from URL")

    args = parser.parse_args()

    if args.command == "setup":
        setup_wizard()
    elif args.command == "clip":
        title, content = args.title, args.content
        if args.direct:
            title_ext, content_ext = extract_content(args.url)
            title = title or title_ext
            content = content or content_ext
        
        if not title or not content:
            print("Error: Title and Content are required (or use --direct).")
            sys.exit(1)
            
        clip(args.url, title, content, args.folder, args.tags, args.metadata, args.mode)
    else:
        parser.print_help()
