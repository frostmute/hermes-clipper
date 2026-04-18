#!/usr/bin/env /usr/bin/python3
import os
import sys
import datetime
import argparse
import re
import json
import subprocess
import secrets
import platform
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
PID_FILE = CONFIG_DIR / "bridge.pid"

# Ensure config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
# print(f"DEBUG: PID_FILE is {PID_FILE}")

def is_running(pid):
    """Check if a process with given PID is running and matches our name."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    
    # Verify process name to prevent PID reuse issues
    try:
        # Try /proc on Linux first (fastest)
        proc_cmdline = Path(f"/proc/{pid}/cmdline")
        if proc_cmdline.exists():
            with open(proc_cmdline, "rb") as f:
                content = f.read().decode().replace('\x00', ' ').lower()
                return "python" in content or "hermes" in content
        
        # Fallback to 'ps' command
        cmd = ["ps", "-p", str(pid), "-o", "args="]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            args = result.stdout.lower()
            return "python" in args or "hermes" in args
    except Exception:
        # If we can't verify name, we trust os.kill(pid, 0)
        pass
        
    return True

def write_pid(pid):
    with open(PID_FILE, "w") as f:
        f.write(str(pid))

def stop_bridge():
    if PID_FILE.exists():
        with open(PID_FILE, "r") as f:
            try:
                pid = int(f.read().strip())
                if is_running(pid):
                    os.kill(pid, 15)  # SIGTERM
                    print_header(f"Stopped bridge (PID: {pid})")
                else:
                    print_error("Bridge PID file exists but process is not running.")
            except:
                print_error("Invalid PID file.")
        PID_FILE.unlink(missing_ok=True)
    else:
        print_error("Bridge is not running (no PID file).")

def get_bridge_status():
    if PID_FILE.exists():
        try:
            with open(PID_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    PID_FILE.unlink(missing_ok=True)
                    return "offline"
                pid = int(content)
                if is_running(pid):
                    return f"online (PID: {pid})"
                else:
                    # Stale PID file
                    PID_FILE.unlink(missing_ok=True)
        except (ValueError, OSError):
            PID_FILE.unlink(missing_ok=True)
    return "offline"

def start_daemon(host, port):
    if get_bridge_status() != "offline":
        print_error("Bridge is already running.")
        return

    # Use the current python executable to run the 'serve' command
    cmd = [sys.executable, "-m", "hermes_clipper.main", "serve", "--host", host, "--port", str(port)]
    # Start process in a new session (daemon-lite)
    env = os.environ.copy()
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                               start_new_session=True, env=env)
    
    write_pid(process.pid)
    print_header(f"Bridge started in background (PID: {process.pid})")
    print(f"📡 Listening on http://{host}:{port}")

DEFAULT_TEMPLATE = """---
title: "{{title}}"
source: {{url}}
author: "{{author}}"
site: "{{site_name}}"
banner: "{{banner}}"
clipped: {{date}}
published: {{published_date}}
description: "{{description}}"
tags: [{{tags}}]
status: unread
---

# {{title}}

{{content}}
"""

def extract_json_ld(soup):
    try:
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") in ["Article", "NewsArticle", "BlogPosting", "WebPage"]:
                            return item
                elif data.get("@type") in ["Article", "NewsArticle", "BlogPosting", "WebPage"]:
                    return data
            except: continue
    except: pass
    return {}

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
    # repo_root is 3 levels up from src/hermes_clipper/main.py
    repo_root = Path(__file__).parent.parent.parent.absolute()
    
    candidates = [
        repo_root / "skills" / "clipping" / "SKILL.md",
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
    
    print(f"\n🔑 {HERMES_GOLD}Your API Key:{RESET} {BOLD}{config['api_key']}{RESET}")
    print("  Link established. Browser extension will auto-discover this if Host is setup.")

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

def setup_browser_host():
    print_header("Setting up Browser Native Messaging Host")
    
    # repo_root is 3 levels up from src/hermes_clipper/main.py
    repo_root = Path(__file__).parent.parent.parent.absolute()
    src_path = repo_root / "src"
    
    wrapper_path = CONFIG_DIR / "hermes-clip-host"
    
    # 1. Create wrapper script
    # This wrapper ensures PYTHONPATH is set correctly so host.py can find hermes_clipper package
    wrapper_content = f"""#!/bin/bash
export PYTHONPATH="{src_path}"
exec {sys.executable} -m hermes_clipper.host "$@"
"""
    try:
        with open(wrapper_path, "w") as f:
            f.write(wrapper_content)
        wrapper_path.chmod(0o755)
        print(f"Created wrapper script at {wrapper_path}")
    except Exception as e:
        print_error(f"Failed to create wrapper script: {e}")
        return
    
    # 2. Generate Manifest
    # Note: Firefox uses allowed_extensions, Chrome uses allowed_origins
    manifest = {
        "name": "com.frostmute.hermes_clipper",
        "description": "Hermes Clipper Native Messaging Host",
        "path": str(wrapper_path),
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://jkolhkofpogidpceolajclmjdclonlhp/", # Common Dev ID
            "chrome-extension://pgafcinpgbegeedaclnmpleebjeoccla/"  # Placeholder
        ],
        "allowed_extensions": [
            "hermes-clipper@frostmute.io"
        ]
    }
    
    # 3. Detect OS and set target directories
    system = platform.system()
    targets = []
    
    if system == "Linux":
        chrome_base = Path.home() / ".config" / "google-chrome"
        brave_base = Path.home() / ".config" / "BraveSoftware" / "Brave-Browser"
    elif system == "Darwin": # MacOS
        chrome_base = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
        brave_base = Path.home() / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser"
    else:
        print_error(f"OS {system} not supported for auto-setup.")
        return

    # Handle Chrome
    targets.append(chrome_base / "NativeMessagingHosts")
    
    # Handle Brave if folder exists
    if brave_base.exists():
        targets.append(brave_base / "NativeMessagingHosts")
    
    # Also handle Chromium on Linux if it exists
    if system == "Linux":
        chromium_base = Path.home() / ".config" / "chromium"
        if chromium_base.exists():
            targets.append(chromium_base / "NativeMessagingHosts")

    manifest_filename = "com.frostmute.hermes_clipper.json"
    
    success_count = 0
    for target in targets:
        try:
            target.mkdir(parents=True, exist_ok=True)
            manifest_path = target / manifest_filename
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=4)
            print(f"Installed manifest to {manifest_path}")
            success_count += 1
        except Exception as e:
            print_error(f"Failed to install manifest to {target}: {e}")

    if success_count > 0:
        print_header("Browser host setup complete.")
    else:
        print_error("Failed to install manifest to any browser directory.")

def extract_content(url):
    from .extractor import extract_content_to_markdown
    if not HAS_EXTRACTION:
        print_error("'requests', 'beautifulsoup4', and 'readability-lxml' required for direct mode.")
        sys.exit(1)
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else "Untitled"
        
        # Meta mapping for cleaner extraction
        meta_map = {
            "banner": [{"property": "og:image"}],
            "site_name": [{"property": "og:site_name"}],
            "description": [{"name": "description"}, {"property": "og:description"}],
            "author": [{"name": "author"}, {"property": "article:author"}],
            "pub_date": [{"property": "article:published_time"}, {"name": "publish_date"}]
        }
        
        res = {k: "" for k in meta_map}
        for key, attrs_list in meta_map.items():
            for attrs in attrs_list:
                tag = soup.find("meta", attrs=attrs)
                if tag:
                    res[key] = tag.get("content", "")
                    break

        # Schema.org / JSON-LD override
        json_ld = extract_json_ld(soup)
        if json_ld:
            author_ld = json_ld.get("author")
            res["author"] = (author_ld.get("name") if isinstance(author_ld, dict) else author_ld) or res["author"]
            res["pub_date"] = json_ld.get("datePublished") or res["pub_date"]
            res["description"] = json_ld.get("description") or res["description"]

        # Use new markdown extractor
        content = extract_content_to_markdown(response.text)
        
        return {
            "title": title,
            "content": content,
            "banner": res["banner"],
            "site_name": res["site_name"],
            "author": res["author"],
            "description": res["description"],
            "published_date": res["pub_date"]
        }
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

def clip(url, title, content, folder="Clippings", tags=None, metadata=None, mode="unique", caveman=False, banner="", author="", site_name="", description="", published_date=""):
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
                       .replace("{{author}}", author or "")\
                       .replace("{{site_name}}", site_name or "")\
                       .replace("{{description}}", description or "")\
                       .replace("{{published_date}}", published_date or "")\
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
    subparsers.add_parser("setup-browser-host", help="Setup Browser Native Messaging Host")
    
    serve_parser = subparsers.add_parser("serve", help="Start the local bridge server")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8088)
    serve_parser.add_argument("--daemon", action="store_true", help="Start bridge in the background")
    
    subparsers.add_parser("stop", help="Stop the background bridge server")
    subparsers.add_parser("status", help="Check bridge server status")

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
    elif args.command == "setup-browser-host":
        setup_browser_host()
    elif args.command == "serve":
        if args.daemon:
            start_daemon(args.host, args.port)
        else:
            # Write PID for manual serve too
            with open(PID_FILE, "w") as f:
                f.write(str(os.getpid()))
            import atexit
            atexit.register(lambda: PID_FILE.unlink(missing_ok=True))
            
            from hermes_clipper.server import start_server
            start_server(host=args.host, port=args.port)
    elif args.command == "stop":
        stop_bridge()
    elif args.command == "status":
        print(f"Hermes Bridge is {HERMES_GOLD}{get_bridge_status()}{RESET}")
    elif args.command == "agent-clip":
        print(json.dumps(agent_clip(args.url, args.folder, args.prompt, args.mode), indent=2))
    elif args.command == "synthesize":
        print(json.dumps(synthesize_clip(args.path, args.prompt), indent=2))
    elif args.command == "clip":
        title, content, banner = args.title, args.content, ""
        author, site_name, description, published_date = "", "", "", ""
        if args.direct:
            ext = extract_content(args.url)
            title = title or ext.get("title")
            content = content or ext.get("content")
            banner = ext.get("banner")
            author = ext.get("author")
            site_name = ext.get("site_name")
            description = ext.get("description")
            published_date = ext.get("published_date")
        if not title or not content:
            print_error("Title and Content required.")
            sys.exit(1)
        clip(args.url, title, content, args.folder, args.tags, args.metadata, args.mode, args.caveman, 
             banner=banner, author=author, site_name=site_name, description=description, published_date=published_date)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
_main__":
    main()
         print_error("Title and Content required.")
            sys.exit(1)
        clip(args.url, title, content, args.folder, args.tags, args.metadata, args.mode, args.caveman, 
             banner=banner, author=author, site_name=site_name, description=description, published_date=published_date)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
