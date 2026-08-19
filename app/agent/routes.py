from fastapi import APIRouter
from pydantic import BaseModel
from app.agent.agent import run_agent

router = APIRouter(prefix = "/agent", tags = ["agent"])

class AgentQuery(BaseModel):
    message:str


@router.post("/ask")
def ask_agent(query:AgentQuery):
    return {"response":run_agent(query.message)}