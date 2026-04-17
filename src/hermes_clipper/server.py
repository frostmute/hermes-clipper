import uvicorn
import uuid
import json
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from .main import clip as run_clip, agent_clip as run_agent_clip, synthesize_clip

# Global task storage
tasks: Dict[str, dict] = {}

app = FastAPI(title="Hermes Clipper Bridge")

# Allow CORS for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ClipRequest(BaseModel):
    url: str
    title: str
    content: str
    folder: Optional[str] = "Clippings"
    tags: Optional[List[str]] = []
    mode: Optional[str] = "unique"
    metadata: Optional[dict] = {}

class AgentClipRequest(BaseModel):
    url: str
    folder: Optional[str] = "Clippings"
    prompt: Optional[str] = None

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

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found. Did it even exist?")
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

@app.post("/clip")
async def clip_endpoint(request: ClipRequest):
    try:
        tag_str = ",".join(request.tags) if request.tags else ""
        meta_json = json.dumps(request.metadata) if request.metadata else None
        
        result = run_clip(
            url=request.url,
            title=request.title,
            content=request.content,
            folder=request.folder,
            tags=tag_str,
            metadata=meta_json,
            mode=request.mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/clip")
async def agent_clip_endpoint(request: AgentClipRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "queued", "type": "agent_clip", "url": request.url}
    
    background_tasks.add_task(
        run_background_agent, 
        task_id, 
        run_agent_clip, 
        url=request.url, 
        folder=request.folder, 
        extra_prompt=request.prompt
    )
    
    return {
        "status": "accepted", 
        "task_id": task_id, 
        "message": "Agent dispatched. Try not to get impatient."
    }

@app.post("/agent/synthesize")
async def synthesize_endpoint(request: SynthesizeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "queued", "type": "synthesize", "path": request.path}

    background_tasks.add_task(
        run_background_agent,
        task_id,
        synthesize_clip,
        note_path=request.path,
        extra_prompt=request.prompt
    )

    return {
        "status": "accepted", 
        "task_id": task_id, 
        "message": "Synthesis started. Hermes is thinking deep thoughts."
    }

def start_server(host: str = "127.0.0.1", port: int = 8088):
    from .main import HERMES_LOGO
    print(HERMES_LOGO)
    print(f"📡 Bridge listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
