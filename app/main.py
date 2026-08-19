from fastapi import FastAPI
from app.routes import router as books_router
from app.agent.routes import router as agent_router
app = FastAPI(title = "My life be like.")
app.include_router(books_router)
app.include_router(agent_router)
