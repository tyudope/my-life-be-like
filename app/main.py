from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routes import router as books_router
from app.agent.routes import router as agent_router

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title = "My life be like.")
app.include_router(books_router)
app.include_router(agent_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")
