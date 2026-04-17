import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import os
import json
from .main import clip as run_clip, agent_clip as run_agent_clip

app = FastAPI(title="Hermes Clipper Bridge")

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

@app.get("/")
async def root():
    return {"status": "online", "message": "Hermes Clipper Bridge is running."}

@app.post("/clip")
async def clip_endpoint(request: ClipRequest):
    try:
        # Convert tags list to comma-separated string for the existing clip function
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
async def agent_clip_endpoint(request: AgentClipRequest):
    try:
        # Note: In a production environment, this should ideally be a background task
        # as agent research can take 1-2 minutes, which might exceed client timeouts.
        result = run_agent_clip(
            url=request.url,
            folder=request.folder,
            extra_prompt=request.prompt
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_server(host: str = "127.0.0.1", port: int = 8088):
    print(f"Starting Hermes Clipper Bridge on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
