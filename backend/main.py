import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database.session import init_db
from backend.orchestrator.worker import AutonomousWorker
from backend.api.routes import router, set_worker
from backend.api.websocket import ws_manager

# Global worker instance
worker = AutonomousWorker(
    db_path=str(settings.base_dir / "data" / "viddy.db"),
    storage_dir=str(settings.output_dir),
    cycle_delay_seconds=settings.min_cycle_delay_seconds
)
set_worker(worker)

# Broadcast worker events to connected WebSocket clients
def forward_event_to_ws(event: dict):
    asyncio.create_task(ws_manager.broadcast(event))

worker.subscribe(forward_event_to_ws)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure DB and tables initialized
    init_db()
    from backend.database.session import get_db
    from backend.database import crud
    with get_db() as session:
        # Unconditionally recover any abandoned jobs or orphaned states
        worker.recovery_mgr.recover_interrupted_jobs(session)
        st = crud.get_settings(session)
        # By default in continuous autonomous mode: auto-start unless specifically paused
        if st.running_mode != "paused":
            asyncio.create_task(worker.start())
    yield
    # Shutdown: cleanly stop in-memory tasks without resetting continuous mode in DB
    await worker.stop(persist=False)

app = FastAPI(
    title="Viddy Autonomous AI Video Studio",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach API routes
app.include_router(router)

# WebSocket streaming endpoint
@app.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial status snapshot immediately on connect
        from backend.api.routes import get_agent_status
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "data": get_agent_status()
        })
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

# Mount media directory for video streaming
media_dir = settings.output_dir
media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

# Mount frontend dist if exists
frontend_dist = settings.base_dir / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
