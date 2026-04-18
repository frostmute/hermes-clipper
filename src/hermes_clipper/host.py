#!/usr/bin/env python3
import sys
import json
import struct
import time
import os
import requests
import contextlib
import io

# Import from main, but we must be careful about stdout
try:
    from hermes_clipper.main import get_bridge_status, start_daemon, load_config
except ImportError:
    # Handle cases where it's run as a script without proper pythonpath
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from hermes_clipper.main import get_bridge_status, start_daemon, load_config

# Native Messaging Protocol
def get_message():
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        return None
    message_length = struct.unpack('@I', raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode('utf-8')
    return json.loads(message)

def send_message(message_dict):
    content = json.dumps(message_dict).encode('utf-8')
    length = struct.pack('@I', len(content))
    sys.stdout.buffer.write(length)
    sys.stdout.buffer.write(content)
    sys.stdout.buffer.flush()

def main():
    config = load_config()
    api_key = config.get("api_key")

    while True:
        try:
            message = get_message()
            if message is None:
                break
            
            # Implementation logic
            # If bridge is offline, call start_daemon and wait a bit
            if get_bridge_status() == "offline":
                # Suppress stdout to avoid corrupting native messaging protocol
                with contextlib.redirect_stdout(io.StringIO()):
                    try:
                        start_daemon("127.0.0.1", 8088)
                    except Exception:
                        pass
                time.sleep(2) # Wait for server to initialize
            
            # Forward the request to http://localhost:8088/clip
            try:
                # Use a reasonable timeout
                headers = {}
                if api_key:
                    headers["X-API-Key"] = api_key
                
                response = requests.post(
                    "http://127.0.0.1:8088/clip", 
                    json=message, 
                    headers=headers,
                    timeout=30
                )
                send_message(response.json())
            except requests.exceptions.RequestException as e:
                send_message({
                    "status": "error",
                    "message": f"Failed to connect to bridge: {str(e)}"
                })
                
        except Exception as e:
            # If we hit a protocol error or other major issue, exit
            # We can't really "log" to stdout, so we just exit
            break

if __name__ == "__main__":
    main()
