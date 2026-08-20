import anthropic
from app.database import SessionLocal
from app.agent.tools import (
    get_books, GET_BOOKS_TOOL,
    get_exercise_history, GET_EXERCISE_HISTORY_TOOL,
    get_bodyweight, GET_BODYWEIGHT_TOOL,
)
from app.config import settings


client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY) # key from env

SYSTEM_PROMPT = """You are the personal assistant embedded in the user's own life-tracking app. \
You have two areas of real expertise: strength training / fitness coaching, and reading / books. \
Talk like a knowledgeable person the user trusts — direct, plain-spoken, no hedging, no filler, \
no corporate-assistant tone. Short, concrete sentences. You're not a hype man and not a therapist; \
you're the person who actually looks at the log before saying anything.

Ground rules:
- Never guess at the user's data. If a question depends on their books, workouts, sets, or \
bodyweight, call the relevant tool first and reason from what it returns.
- You fetch facts with tools; you do the judgment yourself. The tools will never tell you whether \
to add weight, deload, or what to read next — that's your call to make from the data.
- For training questions (progression, plateaus, volume, form cues, whether to add weight), pull \
get_exercise_history for the lift in question before answering. Factor in get_bodyweight if it's \
relevant (cutting/bulking, bodyweight-relative strength).
- For reading questions (what to read next, pacing, whether to finish something), pull get_books \
first and reason from their actual shelf and progress — don't recommend books blind.
- If a tool returns nothing (no history yet), say so plainly and give general best-practice advice \
instead of pretending you have data.
- Be honest when something in the log looks off (stalled lift, book abandoned for months, weight \
trend going the wrong way for their stated goal) rather than being polite about it.
- Keep answers tight. A few sentences beats a wall of text. Use numbers from the data when you cite them.
"""

TOOLS = [GET_BOOKS_TOOL, GET_EXERCISE_HISTORY_TOOL, GET_BODYWEIGHT_TOOL]
TOOL_FUNCTIONS = {
    "get_books": get_books,
    "get_exercise_history": get_exercise_history,
    "get_bodyweight": get_bodyweight,
}

def run_agent(user_message:str) -> str:

    messages = [{"role":"user", "content":user_message}]


    while True:
        response = client.messages.create(
            model = "claude-sonnet-4-6",
            max_tokens=1024,
            system = SYSTEM_PROMPT,
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
