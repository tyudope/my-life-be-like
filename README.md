# My Life Be Like

A personal life-tracking app for the three things I actually want to keep score of —
**books, bodyweight, and lifts** — with a Claude-powered advisor sitting next to the
data that reads the log before it says anything.

The point isn't another tracker. It's that the advice is grounded: when you ask
*"should I add weight to bench?"*, the model doesn't guess — it calls a tool, pulls
your actual last twelve sets out of Postgres, and answers from those numbers.

```
> should I add weight to bench?
advisor  You've hit 3×8 at 80kg three sessions running, last one on the 14th.
         That's not a plateau, that's a green light. Go 82.5 and expect 6-7 reps
         on the last set.
```

---

## What's in it

**Tracking**
- **Books** — title, total pages, pages read. Progress is derived, never a checkbox.
- **Bodyweight** — timestamped log with a trend you can actually read.
- **Workouts** — a workout is a named session; inside it, sets of an exercise with
  weight, reps, and set number. Log a new session from a saved "routine" (a previous
  workout's structure) and it pre-fills your last known numbers.
- **History & progress** — session history, plus an SVG chart per exercise (top set
  weight, total volume, or total reps) drawn by hand, no chart library.

**The advisor**
- A terminal-style panel wired to `POST /agent/ask`.
- Three read-only tools: `get_books`, `get_exercise_history`, `get_bodyweight`.
- The system prompt's hard rule: never guess at the user's data — call the tool first.
  Tools fetch facts; the *model* does the judgment. There is no "should I deload"
  logic in Python, on purpose.

**The frontend** is a single hand-written `index.html` — no framework, no bundler,
no npm. Amber-on-black, monospace, looks like an ops console.

---

## Stack

| | |
|---|---|
| API | FastAPI (sync routes) |
| ORM | SQLAlchemy 2.0, `Mapped` / `mapped_column` style |
| Validation | Pydantic v2 (`extra="forbid"` everywhere) |
| DB | PostgreSQL 16 via Docker Compose, `psycopg` driver |
| AI | Anthropic Claude API with tool use (`claude-sonnet-4-6`) |
| Config | pydantic-settings, `.env` |
| UI | One static HTML file, vanilla JS |
| Python | 3.11 |

---

## Setup

**1. Clone and install**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Configure**

```bash
cp .env.example .env
```

Then fill in `.env`:

| Variable | What it's for |
|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | credentials Docker Compose creates the database with |
| `DB_PORT` | host port mapped to Postgres (`5435` by default, to stay out of the way of a local 5432) |
| `DATABASE_URL` | what the app connects with — must match the four above, e.g. `postgresql+psycopg://user:pass@localhost:5435/mylifebelike` |
| `ANTHROPIC_API_KEY` | your key from [console.anthropic.com](https://console.anthropic.com/) |

`.env` is gitignored. Don't commit it.

**3. Start the database**

```bash
docker compose up -d
```

**4. Create the tables**

```bash
python -m app.create_tables
```

**5. Run**

```bash
uvicorn app.main:app --reload
```

- Dashboard → <http://127.0.0.1:8000/>
- Interactive API docs → <http://127.0.0.1:8000/docs>

---

## API

Every entity gets the same five routes. Collection paths have **no trailing slash**.

| Method | Path | Body / Result |
|---|---|---|
| `POST` | `/books` | `{name, total_page, completed_page?}` → `BookRead` |
| `GET` | `/books` | list of `BookRead` |
| `GET` | `/books/{id}` | `BookRead`, 404 if missing |
| `PATCH` | `/books/{id}` | any subset of `{name, total_page, completed_page}` |
| `DELETE` | `/books/{id}` | `204`, no body |

Same shape for:

| Prefix | Create body |
|---|---|
| `/bodyweight` | `{weight}` |
| `/exercises` | `{name}` |
| `/workouts` | `{name}` |
| `/sets` | `{weight, set_number, reps, workout_id, exercise_id}` |

Server-set fields (`id`, `created_at`, `date`) are never accepted on create or update —
they come back on read. Unknown fields are rejected outright (`extra="forbid"`).

**The agent**

```http
POST /agent/ask
{ "message": "how's my reading going?" }

→ { "response": "You're 240 pages into Dune out of 412..." }
```

Single-turn: each request starts a fresh conversation. There's no memory between calls.

---

## How the agent works

`run_agent()` in `app/agent/agent.py` is a plain tool-use loop:

1. Send the user's message with `TOOLS` attached.
2. If `stop_reason != "tool_use"` → that's the answer, return it.
3. Otherwise, run every `tool_use` block the model asked for — each gets its own
   database session — and send all the `tool_result` blocks back in one user message.
4. Repeat until the model stops asking for tools.

Adding a tool is three pieces, all in `app/agent/tools.py` + `agent.py`:

```python
def get_thing(db: Session, some_arg: str, limit: int = 20):
    ...
    return [{"field": row.field} for row in rows]   # clean dicts, not ORM rows

GET_THING_TOOL = {
    "name": "get_thing",
    "description": "What it returns AND when the model should reach for it.",
    "input_schema": {...},        # note: `db` never appears here
}

TOOLS = [..., GET_THING_TOOL]
TOOL_FUNCTIONS = {..., "get_thing": get_thing}
```

Two rules that matter more than the rest:

- **`db` is injected by the loop, not by the model** — it's the first parameter of the
  function and it must not appear in `input_schema`.
- **Tools fetch, the model decides.** A tool returns the last 20 bench sets. It does
  not return "you should add 2.5kg". The moment judgment moves into Python, the model
  stops being an advisor and starts being a mouthpiece for a hardcoded rule.

---

## Project layout

```
app/
├── main.py             FastAPI app, routers, static mount, "/" → dashboard
├── config.py           Settings (pydantic-settings)
├── database.py         engine, SessionLocal, get_db, Base
├── models.py           all SQLAlchemy tables
├── schemas.py          all Pydantic schemas (Create / Read / Update per entity)
├── routes.py           CRUD routers for all five entities
├── create_tables.py    Base.metadata.create_all
├── static/
│   └── index.html      the entire frontend
└── agent/
    ├── tools.py        tool functions + tool-schema dicts
    ├── agent.py        run_agent loop, system prompt, TOOLS, TOOL_FUNCTIONS
    └── routes.py       POST /agent/ask
```

Data model:

```
Book        (id, name, total_page, completed_page, created_at)
BodyWeight  (id, weight, date)
Exercise    (id, name)
Workout     (id, name, date) ──< ExerciseSet >── Exercise
ExerciseSet (id, weight, set_number, reps, workout_id, exercise_id)
```

Deleting a workout deletes its sets (`cascade="all, delete-orphan"`) — a set has no
meaning without the session it belonged to.

---

## Known limits

This runs on localhost for one person, and it's built that way:

- No auth, no rate limiting, no CORS setup.
- No migrations (`create_all` only) and no tests.
- Deleting an exercise that still has sets logged against it fails on the foreign key.
- No validation stopping `completed_page > total_page` or a negative weight.
- The agent is read-only and has no memory across requests.

## Roadmap

- Write tools for the agent ("log today's session from what I just told you")
- Conversation memory in the advisor panel
- Actual validation pass on the schemas
- Alembic, once the schema stops moving
