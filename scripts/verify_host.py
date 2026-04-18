import struct
import json
import subprocess
import time
import os
import sys

def send_msg(proc, msg):
    content = json.dumps(msg).encode('utf-8')
    length = struct.pack('@I', len(content))
    proc.stdin.write(length)
    proc.stdin.write(content)
    proc.stdin.flush()

def recv_msg(proc):
    raw_length = proc.stdout.read(4)
    if not raw_length:
        return None
    length = struct.unpack('@I', raw_length)[0]
    content = proc.stdout.read(length).decode('utf-8')
    return json.loads(content)

# Start host.py
env = os.environ.copy()
env["PYTHONPATH"] = "src"
proc = subprocess.Popen(
    ["/home/frost/hermes-clipper/.venv/bin/python3", "src/hermes_clipper/host.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd="/home/frost/hermes-clipper",
    env=env
)

# Send a test message
test_msg = {
    "url": "https://example.com",
    "title": "Example",
    "content": "This is a test clip from Native Messaging Host.",
    "folder": "Clippings",
    "tags": ["test", "native-messaging"],
    "mode": "unique"
}

print("Sending message...")
send_msg(proc, test_msg)

# Wait for response
print("Waiting for response (might start daemon)...")
start_time = time.time()
response = recv_msg(proc)
end_time = time.time()

if response:
    print(f"Response (took {end_time - start_time:.2f}s):", json.dumps(response, indent=2))
else:
    print("No response received. Checking stderr...")
    stderr = proc.stderr.read().decode('utf-8')
    print("Stderr:", stderr)

# Clean up
proc.terminate()

# Also stop the bridge if we started it, to keep environment clean
subprocess.run(["/home/frost/hermes-clipper/.venv/bin/python3", "-m", "hermes_clipper.main", "stop"], 
               cwd="/home/frost/hermes-clipper", env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
