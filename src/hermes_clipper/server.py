import uvicorn
import uuid
import json
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from .main import clip as run_clip, agent_clip as run_agent_clip, synthesize_clip, load_config
from .watcher import VaultWatcher

# Global task storage
tasks: Dict[str, dict] = {}
vault_watcher: Optional[VaultWatcher] = None

app = FastAPI(title="Hermes Clipper Bridge")

@app.on_event("startup")
async def startup_event():
    global vault_watcher
    config = load_config()
    vault_path = config.get("vault_path")
    if vault_path:
        vault_watcher = VaultWatcher(vault_path)
        vault_watcher.start()

@app.on_event("shutdown")
async def shutdown_event():
    global vault_watcher
    if vault_watcher:
        vault_watcher.stop()

# Security: Restrict CORS to known origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "app://obsidian.md",
    ],
    allow_origin_regex="chrome-extension://.*",
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

async def verify_api_key(x_api_key: str = Header(...)):
    config = load_config()
    expected_key = config.get("api_key")
    if not expected_key:
        raise HTTPException(status_code=500, detail="Bridge not configured. Run 'hermes-clip setup'.")
    if x_api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API Key. Hermes is not impressed.")
    return x_api_key

class ClipRequest(BaseModel):
    url: str
    title: str
    content: str
    folder: Optional[str] = "Clippings"
    tags: Optional[List[str]] = []
    mode: Optional[str] = "unique"
    metadata: Optional[dict] = {}
    banner: Optional[str] = ""

class AgentClipRequest(BaseModel):
    url: str
    folder: Optional[str] = "Clippings"
    prompt: Optional[str] = None
    mode: Optional[str] = "unique"

class SynthesizeRequest(BaseModel):
    path: str
    prompt: Optional[str] = None

@app.get("/")
async def root():
    return {
        "status": "online", 
        "message": "Hermes is judging your bookmarks.", 
        "active_tasks": len(tasks)
    }

@app.get("/tasks/{task_id}", dependencies=[Depends(verify_api_key)])
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found.")
    return tasks[task_id]

def run_background_agent(task_id: str, func, **kwargs):
    try:
        tasks[task_id]["status"] = "processing"
        result = func(**kwargs)
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)

@app.post("/clip", dependencies=[Depends(verify_api_key)])
async def clip_endpoint(request: ClipRequest):
    try:
        tag_str = ",".join(request.tags) if request.tags else ""
        meta_json = json.dumps(request.metadata) if request.metadata else None
        return run_clip(request.url, request.title, request.content, request.folder, tag_str, meta_json, request.mode, banner=request.banner)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/clip", dependencies=[Depends(verify_api_key)])
async def agent_clip_endpoint(request: AgentClipRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "queued", "type": "agent_clip", "url": request.url}
    background_tasks.add_task(run_background_agent, task_id, run_agent_clip, url=request.url, folder=request.folder, extra_prompt=request.prompt, mode=request.mode)
    return {"status": "accepted", "task_id": task_id}

@app.post("/agent/synthesize", dependencies=[Depends(verify_api_key)])
async def synthesize_endpoint(request: SynthesizeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "queued", "type": "synthesize", "path": request.path}
    background_tasks.add_task(run_background_agent, task_id, synthesize_clip, note_path=request.path, extra_prompt=request.prompt)
    return {"status": "accepted", "task_id": task_id}

def start_server(host: str = "127.0.0.1", port: int = 8088):
    from .main import HERMES_LOGO
    print(HERMES_LOGO)
    print(f"📡 Bridge listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
