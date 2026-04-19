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

def is_running(pid):
    """Check if a process with given PID is running and matches our name."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    
    try:
        proc_cmdline = Path(f"/proc/{pid}/cmdline")
        if proc_cmdline.exists():
            with open(proc_cmdline, "rb") as f:
                content = f.read().decode().replace('\x00', ' ').lower()
                return "python" in content or "hermes" in content
        
        cmd = ["ps", "-p", str(pid), "-o", "args="]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            args = result.stdout.lower()
            return "python" in args or "hermes" in args
    except Exception:
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
                    PID_FILE.unlink(missing_ok=True)
        except (ValueError, OSError):
            PID_FILE.unlink(missing_ok=True)
    return "offline"

def start_daemon(host, port):
    if get_bridge_status() != "offline":
        print_error("Bridge is already running.")
        return

    cmd = [sys.executable, "-m", "hermes_clipper.main", "serve", "--host", host, "--port", str(port)]
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
                f.write("# VAULT STRUCTURE (AUTO-GENERATED)\\n")
                f.write(result.stdout)
            print_header("Vault structural index generated (~/.hermes/memories/VAULT_STRUCTURE.md).")
    except: pass

def deploy_skill():
    hermes_skill_dir = Path.home() / ".hermes" / "skills" / "note-taking" / "clipping"
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
        with open(hermes_env, "r") as f:
            content = f.read()
        if f'OBSIDIAN_VAULT_PATH="{vault_path}"' not in content:
            with open(hermes_env, "a") as f:
                f.write(f'\\nOBSIDIAN_VAULT_PATH="{vault_path}"\\n')
            print_header("Synced vault path to Hermes Agent.")
    
    if "api_key" not in config:
        config["api_key"] = secrets.token_hex(16)
    
    print(f"\\n🔑 {HERMES_GOLD}Your API Key:{RESET} {BOLD}{config['api_key']}{RESET}")
    print("  Link established. Browser extension will auto-discover this if Host is setup.")

    template_path = CONFIG_DIR / "template.md"
    if not template_path.exists():
        with open(template_path, "w") as f:
            f.write(DEFAULT_TEMPLATE)
    
    config["template_path"] = str(template_path)
    save_config(config)
    setup_vault_index(vault_path)
    deploy_skill()
    print_header("Setup Complete!")

def setup_browser_host(extension_id=None):
    print_header("Setting up Browser Native Messaging Host")
    repo_root = Path(__file__).parent.parent.parent.absolute()
    src_path = repo_root / "src"
    wrapper_path = CONFIG_DIR / "hermes-clip-host"
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

    allowed_origins = [
        "chrome-extension://jkolhkofpogidpceolajclmjdclonlhp/",
        "chrome-extension://pgafcinpgbegeedaclnmpleebjeoccla/"
    ]
    if not extension_id:
        print(f"\n{BOLD}Chrome Extension ID is required for Native Messaging.{RESET}")
        print("Find it at chrome://extensions (Enable 'Developer mode').")
        extension_id = input(f"Enter Extension ID (leave blank to skip custom): ").strip()

    if extension_id:
        allowed_origins.append(f"chrome-extension://{extension_id}/")
        print(f"Added extension ID: {HERMES_GOLD}{extension_id}{RESET}")

    manifest = {
        "name": "com.frostmute.hermes_clipper",
        "description": "Hermes Clipper Native Messaging Host",
        "path": str(wrapper_path),
        "type": "stdio",
        "allowed_origins": allowed_origins,
        "allowed_extensions": ["hermes-clipper@frostmute.io"]
    }
    
    system = platform.system()
    targets = []
    if system == "Linux":
        targets.append(Path.home() / ".config" / "google-chrome" / "NativeMessagingHosts")
        targets.append(Path.home() / ".config" / "BraveSoftware" / "Brave-Browser" / "NativeMessagingHosts")
        targets.append(Path.home() / ".config" / "chromium" / "NativeMessagingHosts")
    elif system == "Darwin":
        targets.append(Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts")
        targets.append(Path.home() / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "NativeMessagingHosts")

    success_count = 0
    for target in targets:
        try:
            target.mkdir(parents=True, exist_ok=True)
            with open(target / "com.frostmute.hermes_clipper.json", "w") as f:
                json.dump(manifest, f, indent=4)
            success_count += 1
        except: pass
    if success_count > 0:
        print_header("Browser host setup complete.")

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
        content = extract_content_to_markdown(response.text)
        
        # Try to extract more metadata
        meta = extract_json_ld(soup)
        
        return {
            "title": title, 
            "content": content,
            "author": meta.get("author", {}).get("name") if isinstance(meta.get("author"), dict) else meta.get("author", ""),
            "site_name": meta.get("publisher", {}).get("name") if isinstance(meta.get("publisher"), dict) else meta.get("name", ""),
            "description": meta.get("description", ""),
            "published_date": meta.get("datePublished", "")
        }
    except Exception as e:
        print_error(f"Extraction failed: {e}")
        sys.exit(1)

def sanitize_filename(title):
    clean = re.sub(r'[\\\\/*?:"<>|]', "", title).strip()
    return clean[:150]

def check_duplicate(url, vault):
    if not url or not vault: return None
    clippings_dir = os.path.join(vault, "Clippings")
    if not os.path.exists(clippings_dir):
        return None
    try:
        patterns = [f"source: {url}", f'source: "{url}"']
        for pattern in patterns:
            # Use fixed strings (-F) for URL search to avoid regex issues
            # Only search within Clippings directory to avoid false positives
            cmd = ["grep", "-rlF", pattern, clippings_dir]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.splitlines()[0]
    except: pass
    return None

def clip(url, title, content, folder="Clippings", tags=None, metadata=None, mode="unique", caveman=False, **kwargs):
    # Aggressive HTML detection
    is_html = False
    stripped_content = content.strip()
    if stripped_content.startswith("<") or "<html" in content.lower() or "<body" in content.lower() or "<div" in content.lower() or "<p" in content.lower() or "<script" in content.lower():
        is_html = True
    
    if is_html:
        try:
            from .extractor import extract_content_to_markdown
            content = extract_content_to_markdown(content)
        except Exception as e:
            print_error(f"HTML extraction failed: {e}")

    config = load_config()
    vault = config.get("vault_path")
    if not vault:
        print_error("Vault path not set. Run 'hermes-clip setup'.")
        sys.exit(1)

    print_header(f"Clipping: {title}")

    if mode == "unique":
        if dup := check_duplicate(url, vault):
            print(json.dumps({"status": "exists", "path": dup}))
            return {"status": "exists", "path": dup}

    filename = sanitize_filename(title)
    target_dir = os.path.join(vault, folder)
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, f"{filename}.md")
    
    template = DEFAULT_TEMPLATE
    
    # Load custom template if it exists
    template_path = config.get("template_path")
    if template_path and os.path.exists(template_path):
        with open(template_path, "r") as f:
            template = f.read()

    tag_list = ["clipping"]
    if tags:
        tag_list.extend([t.strip() for t in tags.split(",")])
    tag_str = ", ".join(tag_list)
    
    replacements = {
        "title": title,
        "url": url,
        "content": content,
        "date": str(datetime.date.today()),
        "tags": tag_str,
        "author": "",
        "site_name": "",
        "description": "",
        "published_date": "",
        "banner": ""
    }
    
    # Merge metadata if provided
    if metadata:
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        if isinstance(metadata, dict):
            replacements.update(metadata)
            
    # Merge kwargs (e.g. banner)
    replacements.update(kwargs)
    
    rendered = template
    for k, v in replacements.items():
        # Handle both {{key}} and {{ key }}
        pattern = re.compile(f"\\{{\\{{\\s*{re.escape(k)}\\s*\\}}\\}}")
        
        # Escape double quotes for YAML frontmatter compatibility
        # We only do this if the value is a string and likely to be in the frontmatter
        # Actually, it's safer to just escape all quotes for the {{placeholder}} replacements
        val = str(v) if v is not None else ""
        if isinstance(v, str):
            val = v.replace('"', '\\"')
            
        rendered = pattern.sub(lambda m, val=val: val, rendered)

    with open(path, "w") as f:
        f.write(rendered)
    
    print(json.dumps({"status": "success", "path": path}))
    return {"status": "success", "path": path}

def agent_clip(url, folder="Clippings", extra_prompt=None, mode="unique"):
    prompt = f"Clip {url} to Obsidian/{folder}."
    if extra_prompt: prompt += f" Note: {extra_prompt}"
    cmd = ["hermes", "chat", "-q", prompt, "-t", "browser,terminal", "-s", "clipping", "--yolo"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {"status": "success", "agent_output": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def synthesize_clip(note_path, extra_prompt=None):
    config = load_config()
    vault = config.get("vault_path")
    
    # Resolve absolute path if relative path was provided
    if vault and not os.path.isabs(note_path):
        abs_path = os.path.join(vault, note_path)
    else:
        abs_path = note_path

    prompt = f"Synthesize {abs_path}."
    if extra_prompt: prompt += f" Note: {extra_prompt}"
    cmd = ["hermes", "chat", "-q", prompt, "-t", "browser,terminal", "-s", "clipping", "--yolo"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {"status": "success", "agent_output": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def show_config():
    config = load_config()
    print_header("Hermes Clipper Configuration")
    for k, v in config.items():
        print(f"  {BOLD}{k}:{RESET} {HERMES_GOLD}{v}{RESET}")

def main():
    parser = argparse.ArgumentParser(description="Hermes Clipper")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("setup")
    subparsers.add_parser("config")
    host_parser = subparsers.add_parser("setup-browser-host", help="Setup Browser Native Messaging Host")
    host_parser.add_argument("--extension-id", help="Optional: Your specific Browser Extension ID")
    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8088)
    serve_parser.add_argument("--daemon", action="store_true")
    subparsers.add_parser("stop")
    subparsers.add_parser("status")
    
    args = parser.parse_args()
    if args.command == "setup": setup_wizard()
    elif args.command == "config": show_config()
    elif args.command == "setup-browser-host": setup_browser_host(args.extension_id)
    elif args.command == "serve":
        if args.daemon: start_daemon(args.host, args.port)
        else:
            from hermes_clipper.server import start_server
            start_server(args.host, args.port)
    elif args.command == "stop": stop_bridge()
    elif args.command == "status": print(get_bridge_status())
    else: parser.print_help()

if __name__ == "__main__":
    main()
