import anthropic
from app.database import SessionLocal
from app.agent.tools import get_books, GET_BOOKS_TOOL
from app.config import settings


client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY) # key from env

TOOLS = [GET_BOOKS_TOOL]
TOOL_FUNCTIONS = {"get_books": get_books}

def run_agent(user_message:str) -> str:

    messages = [{"role":"user", "content":user_message}]


    while True:
        response = client.messages.create(
            model = "claude-sonnet-4-6",
            max_tokens=1024,
            tools = TOOLS,
            messages=messages,
        )


        if response.stop_reason != "tool_use":
            # Clauded gave a final answer
            return response.content[0].text


        # Claudew wants to call one or more tools
        messages.append({"role":"assistant", "content":response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = TOOL_FUNCTIONS[block.name]
                db = SessionLocal()

                try:
                    result = fn(db=db, **block.input) # inject db, spread Claude's args
                finally:
                    db.close()
                tool_results.append({
                    "type":"tool_result",
                    "tool_use_id":block.id,
                    "content":str(result)
                })

        messages.append({"role":"user", "content":tool_results})