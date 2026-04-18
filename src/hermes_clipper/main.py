#!/usr/bin/env /usr/bin/python3
import os
import sys
import datetime
import argparse
import re
import json
import subprocess
import secrets
from pathlib import Path

# --- Branding ---
HERMES_GOLD = "\033[33m"
RESET = "\033[0m"
BOLD = "\033[1m"

HERMES_LOGO = f"""{HERMES_GOLD}{BOLD}
  ⚡ HERMES CLIPPER v0.1.0
  "Too lazy to file it yourself? I got you."
{RESET}"""

def print_header(text):
    print(f"{HERMES_GOLD}{BOLD}>>> {text}{RESET}")

def print_error(text):
    print(f"{HERMES_GOLD}{BOLD}!!! {text} (Smooth move, Einstein.){RESET}")

# --- Logic ---

try:
    from bs4 import BeautifulSoup
    import requests
    from readability import Document
    HAS_EXTRACTION = True
except ImportError:
    HAS_EXTRACTION = False

CONFIG_DIR = Path.home() / ".config" / "hermes-clipper"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_TEMPLATE = """---
title: "{{title}}"
source: {{url}}
banner: "{{banner}}"
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

def setup_vault_index(vault_path):
    index_path = Path.home() / ".hermes" / "memories" / "VAULT_STRUCTURE.md"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        cmd = f'find {vault_path} -mindepth 1 -maxdepth 4 -type d | sed "s|^{vault_path}/||" | grep -v "^\\." | sort'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            with open(index_path, "w") as f:
                f.write("# VAULT STRUCTURE (AUTO-GENERATED)\n")
                f.write(result.stdout)
            print_header("Vault structural index generated (~/.hermes/memories/VAULT_STRUCTURE.md).")
    except: pass

def deploy_skill():
    hermes_skill_dir = Path.home() / ".hermes" / "skills" / "note-taking" / "clipping"
    
    # Discovery chain: check common repo/install locations
    candidates = [
        Path(__file__).parent.parent.parent / "skills" / "clipping" / "SKILL.md",
        Path.home() / "hermes-clipper" / "skills" / "clipping" / "SKILL.md",
        Path("/usr/local/share/hermes-clipper/skills/clipping/SKILL.md"),
    ]
    
    repo_skill = None
    for candidate in candidates:
        if candidate.exists():
            repo_skill = candidate
            break

    if repo_skill:
        hermes_skill_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy(repo_skill, hermes_skill_dir / "SKILL.md")
        print_header(f"Clipper Skill deployed to {hermes_skill_dir}.")
    else:
        print_error("Skill file (SKILL.md) not found in expected locations. Deployment skipped.")

def setup_wizard():
    print(HERMES_LOGO)
    print("Welcome to the Hermes Clipper Setup Wizard!")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = load_config()
    
    default_vault = os.path.expanduser("~/Documents/ObsidianVault")
    current_vault = config.get("vault_path") or os.environ.get("OBSIDIAN_VAULT_PATH", default_vault)
    
    print(f"Current Obsidian Vault path: {HERMES_GOLD}{current_vault}{RESET}")
    vault_path = input(f"Enter new path (leave blank to keep): ").strip() or current_vault
    
    vault_path = os.path.expanduser(vault_path)
    if not os.path.exists(vault_path):
        print(f"Warning: Path {vault_path} does not exist. Creating it...")
        os.makedirs(vault_path, exist_ok=True)
    
    config["vault_path"] = vault_path
    
    hermes_env = Path.home() / ".hermes" / ".env"
    if hermes_env.exists():
        # Avoid duplicate entries
        with open(hermes_env, "r") as f:
            content = f.read()
        if f'OBSIDIAN_VAULT_PATH="{vault_path}"' not in content:
            with open(hermes_env, "a") as f:
                f.write(f'\nOBSIDIAN_VAULT_PATH="{vault_path}"\n')
            print_header("Synced vault path to Hermes Agent.")
    
    if "api_key" not in config:
        config["api_key"] = secrets.token_hex(16)
        print(f"Generated API Key: {HERMES_GOLD}{config['api_key']}{RESET}")
        print("Save this. You'll need it for the extension and plugin.")

    template_path = CONFIG_DIR / "template.md"
    if not template_path.exists():
        with open(template_path, "w") as f:
            f.write(DEFAULT_TEMPLATE)
    
    config["template_path"] = str(template_path)
    save_config(config)

    # Token Efficient Deployments
    setup_vault_index(vault_path)
    deploy_skill()

    print_header("Setup Complete!")
    print(f"\n💡 {HERMES_GOLD}Token Optimization Tip:{RESET}")
    print("  To maximize efficiency, keep 'Caveman Mode' active in Hermes.")
    print("  Run: 'hermes chat -q \"use caveman mode forever\"'")

def extract_content(url):
    if not HAS_EXTRACTION:
        print_error("'requests', 'beautifulsoup4', and 'readability-lxml' required for direct mode.")
        sys.exit(1)
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else "Untitled"
        
        banner = ""
        og_image = soup.find("meta", property="og:image")
        if og_image:
            banner = og_image.get("content", "")

        doc = Document(response.text)
        content_html = doc.summary()
        
        content_soup = BeautifulSoup(content_html, "html.parser")
        content = content_soup.get_text(separator="\n", strip=True)
        
        return title, content, banner
    except Exception as e:
        print_error(f"Extraction failed: {e}")
        sys.exit(1)

def sanitize_filename(title):
    clean = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    return clean[:150]

def check_duplicate(url, vault):
    if not url or not vault: return None
    try:
        # Search for source URL in frontmatter (supports source: URL or source: "URL")
        patterns = [f"source: {url}", f'source: "{url}"']
        for pattern in patterns:
            cmd = ["grep", "-rl", pattern, vault]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                # Return the first match found
                return result.stdout.splitlines()[0]
    except: pass
    return None

def clip(url, title, content, folder="Clippings", tags=None, metadata=None, mode="unique", caveman=False, banner=""):
    config = load_config()
    vault = config.get("vault_path") or os.environ.get("OBSIDIAN_VAULT_PATH")
    
    if not vault:
        print_error("Vault path not set. Run 'hermes-clip setup'.")
        sys.exit(1)

    if mode == "unique":
        dup = check_duplicate(url, vault)
        if dup:
            vault_name = os.path.basename(vault)
            relative_path = os.path.relpath(dup, vault)
            res = {
                "status": "exists",
                "path": dup,
                "uri": f"obsidian://open?vault={vault_name}&file={relative_path}"
            }
            print(json.dumps(res))
            return res
        
    if caveman:
        content = re.sub(r'\b(the|a|an|and|is|are|was|were|to|of|for|in|on|at|by|with)\b', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\s+', ' ', content).strip()

    filename = sanitize_filename(title)
    if not filename:
        filename = "Untitled_Clipping_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
    target_dir = os.path.normpath(os.path.join(vault, folder))
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, f"{filename}.md")
    
    if os.path.exists(path):
        if mode == "unique":
            counter = 1
            while os.path.exists(path):
                path = os.path.join(target_dir, f"{filename}_{counter}.md")
                counter += 1
    
    template_path = config.get("template_path")
    template = DEFAULT_TEMPLATE
    if template_path and os.path.exists(template_path):
        with open(template_path, "r") as f:
            template = f.read()

    tag_list = ["clipping"]
    if tags:
        tag_list.extend([t.strip() for t in tags.strip("[]").split(",")])
    tag_str = ", ".join(list(set(tag_list)))

    rendered = template.replace("{{title}}", title)\
                       .replace("{{url}}", url)\
                       .replace("{{banner}}", banner)\
                       .replace("{{content}}", content)\
                       .replace("{{date}}", str(datetime.date.today()))\
                       .replace("{{tags}}", tag_str)

    if metadata:
        try:
            extra_meta = json.loads(metadata)
            meta_str = "\n".join([f"{k}: {v}" for k, v in extra_meta.items()])
            rendered = rendered.replace("---", f"---\n{meta_str}", 1)
        except: pass

    write_mode = "a" if mode == "merge" and os.path.exists(path) else "w"
    with open(path, write_mode) as f:
        if write_mode == "a":
            f.write(f"\n\n--- \n*Appended on {datetime.datetime.now()}*\n\n{rendered}")
        else:
            f.write(rendered)
    
    vault_name = os.path.basename(vault)
    relative_path = os.path.relpath(path, vault)
    result = {
        "status": "success",
        "path": path,
        "uri": f"obsidian://open?vault={vault_name}&file={relative_path}"
    }
    print(json.dumps(result))
    return result

def agent_clip(url, folder="Clippings", extra_prompt=None, mode="unique"):
    config = load_config()
    vault = config.get("vault_path") or os.environ.get("OBSIDIAN_VAULT_PATH")
    
    if mode == "unique":
        if dup := check_duplicate(url, vault):
            vault_name = os.path.basename(vault)
            relative_path = os.path.relpath(dup, vault)
            return {
                "status": "exists", 
                "path": dup, 
                "uri": f"obsidian://open?vault={vault_name}&file={relative_path}"
            }

    prompt = f"Clip {url} to Obsidian/{folder} (mode: {mode})."
    if extra_prompt: prompt += f" Note: {extra_prompt}"
    if mode == "merge": prompt += " Since mode is merge, append new findings to the existing note if found."
    
    print_header(f"Dispatching Agent: {url}")
    cmd = ["hermes", "chat", "-q", prompt, "-t", "browser,terminal", "-s", "clipping", "--yolo"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {"status": "success", "agent_output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Agent failed: {e.stderr or str(e)}"}

def synthesize_clip(note_path, extra_prompt=None):
    abs_path = os.path.abspath(note_path)
    prompt = f"Synthesize {abs_path}: refine, cross-link, move to perm folder, status: permanent, tag: Synthesized."
    if extra_prompt: prompt += f" Note: {extra_prompt}"
    print_header(f"Dispatching Agent: {note_path}")
    cmd = ["hermes", "chat", "-q", prompt, "-t", "browser,terminal", "-s", "clipping", "--yolo"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {"status": "success", "agent_output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Synthesis failed: {e.stderr or str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="Hermes Clipper for Obsidian")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("setup", help="Run the configuration wizard")
    serve_parser = subparsers.add_parser("serve", help="Start the local bridge server")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8088)
    agent_parser = subparsers.add_parser("agent-clip", help="Dispatch Hermes to research and clip a URL")
    agent_parser.add_argument("--url", required=True)
    agent_parser.add_argument("--folder", default="Clippings")
    agent_parser.add_argument("--prompt", help="Extra instructions for the agent")
    agent_parser.add_argument("--mode", choices=["unique", "merge"], default="unique")
    synth_parser = subparsers.add_parser("synthesize", help="Refine an existing note with Hermes")
    synth_parser.add_argument("--path", required=True)
    synth_parser.add_argument("--prompt", help="Extra instructions for the agent")
    clip_parser = subparsers.add_parser("clip", help="Clip content to Obsidian")
    clip_parser.add_argument("--url", required=True)
    clip_parser.add_argument("--title")
    clip_parser.add_argument("--content")
    clip_parser.add_argument("--folder", default="Clippings")
    clip_parser.add_argument("--tags")
    clip_parser.add_argument("--metadata")
    clip_parser.add_argument("--mode", choices=["unique", "merge", "overwrite"], default="unique")
    clip_parser.add_argument("--direct", action="store_true")
    clip_parser.add_argument("--caveman", action="store_true")

    args = parser.parse_args()
    if args.command == "setup":
        setup_wizard()
    elif args.command == "serve":
        from hermes_clipper.server import start_server
        start_server(host=args.host, port=args.port)
    elif args.command == "agent-clip":
        print(json.dumps(agent_clip(args.url, args.folder, args.prompt, args.mode), indent=2))
    elif args.command == "synthesize":
        print(json.dumps(synthesize_clip(args.path, args.prompt), indent=2))
    elif args.command == "clip":
        title, content, banner = args.title, args.content, ""
        if args.direct:
            title_ext, content_ext, banner_ext = extract_content(args.url)
            title, content, banner = title or title_ext, content or content_ext, banner_ext
        if not title or not content:
            print_error("Title and Content required.")
            sys.exit(1)
        clip(args.url, title, content, args.folder, args.tags, args.metadata, args.mode, args.caveman, banner)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
