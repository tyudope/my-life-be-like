# My Life Be Like — Project Guide

A personal life-tracking app (books, bodyweight, workouts) with a Claude-powered
agent that reads the user's own data via tool use and gives grounded advice.

Single user, single machine, no auth. Optimize for clarity over generality — this
is one person's log, not a SaaS.

## Stack
- Python 3.11, FastAPI, SQLAlchemy 2.0 (`Mapped`/`mapped_column` style), Pydantic v2
- PostgreSQL 16 (via Docker Compose), `psycopg` driver
- Anthropic Claude API (tool use), model pinned in `app/agent/agent.py`
- Frontend: one hand-written `app/static/index.html` — vanilla JS, no build step
- Config via pydantic-settings; secrets in `.env` (gitignored), keys in `.env.example`

## Commands

```bash
source .venv/bin/activate
pip install -r requirements.txt

docker compose up -d              # Postgres; reads POSTGRES_* / DB_PORT from .env
python -m app.create_tables       # create_all — run once, and after adding a model
uvicorn app.main:app --reload     # http://127.0.0.1:8000 → dashboard, /docs → OpenAPI
```

There are no migrations (no Alembic) and no test suite. Schema changes mean either
`create_tables` on a fresh table or hand-written SQL — say so instead of silently
assuming a migration will run.

## Project structure
- `app/models.py` — all SQLAlchemy tables
- `app/schemas.py` — all Pydantic schemas
- `app/routes.py` — CRUD routers (one `APIRouter` per domain, combined into one `router`)
- `app/database.py` — engine, `SessionLocal`, `get_db`, `Base`
- `app/config.py` — `Settings` (+ cached `settings` singleton)
- `app/create_tables.py` — `Base.metadata.create_all`
- `app/main.py` — FastAPI app, router wiring, `/static` mount, `/` → dashboard
- `app/static/index.html` — the entire frontend (markup + CSS + JS in one file)
- `scripts/seed_demo.py` — backfills demo training/bodyweight history (`--wipe` undoes it);
  everything it writes is dated <= 2026-08-18 so it never collides with real sessions
- `docs/screenshots/` — images used by the README
- `app/agent/` — the AI agent
  - `tools.py` — tool functions + their tool-schema dicts
  - `agent.py` — the `run_agent` loop (client, `SYSTEM_PROMPT`, `TOOLS`, `TOOL_FUNCTIONS`)
  - `routes.py` — the `POST /agent/ask` endpoint
  - `client.py` — currently empty; leave it or delete it, don't half-populate it

## Data model

```
Book        (id, name, total_page, completed_page, created_at)
BodyWeight  (id, weight, date)
Exercise    (id, name)
Workout     (id, name, date) ──< ExerciseSet >── Exercise
ExerciseSet (id, weight, set_number, reps, workout_id, exercise_id)
```

- `Workout.sets` is the only ORM relationship, with `cascade="all, delete-orphan"` —
  a set has no meaning without its workout. There is deliberately no
  `ExerciseSet.exercise` relationship; the agent tools join explicitly instead.
- Progress ("is this book done", "is this lift going up") is always **derived** from
  the rows, never stored as a flag.

## Core conventions (follow these exactly)

### Schemas — three shapes per entity
- `XCreate` — only fields the caller provides. No `id`, no server-set fields (e.g. `created_at`, `date`).
- `XRead` — full picture including `id` and timestamps. MUST have `model_config = ConfigDict(from_attributes=True)`.
- `XUpdate` — all fields optional (`T | None = Field(default=None)`), only genuinely editable fields (no `id`, no FKs, no server-set fields).
- All schemas inherit a `StrictModel` base with `extra="forbid"`.
- Rule: annotation controls allowed values, default controls requiredness. `| None` alone does NOT make a field optional — it needs a default too.

### Models
- SQLAlchemy 2.0 style: `Mapped[type]` + `mapped_column(...)`. Let the annotation imply type and nullability; only pass args to `mapped_column` for what the annotation can't express (e.g. `String(50)`, `ForeignKey(...)`, `primary_key=True`, `server_default`).
- Prefer deriving values over storing them (no redundant flags like `is_completed`).
- Foreign keys live on the "many" side.

### Routes — CRUD pattern
- One `APIRouter` per domain with `prefix="/thing"` and `tags=["thing"]`, all combined into the module-level `router` at the bottom of `routes.py`.
- Collection routes are `""`, not `"/"` — so `POST /books`, not `POST /books/`.
- Create: build model with `X(**payload.model_dump())` → add → commit → refresh.
- Update (PATCH): fetch → 404 if None → `payload.model_dump(exclude_unset=True)` → `setattr` each → commit → refresh.
- Delete: fetch → 404 if None → delete → commit → 204, no body.
- Get-one: `db.get(Model, id)`, raise `HTTPException(404)` if None.
- Validate referenced FKs up front (see `create_set`) so the caller gets a clean 404 instead of a raw `IntegrityError` 500.
- Routes are `def` (sync), not `async` — SQLAlchemy's Session and the Claude client are both synchronous, so an `async def` route would block the event loop.

### Agent tools — THE most important conventions
- A tool FETCHES FACTS or takes an action. A tool NEVER does the reasoning/judgment — that is the model's job. (e.g. a tool returns workout history; the MODEL decides whether to add weight. Do NOT put "should I add weight" logic in Python.)
- Each tool = (1) a query function, (2) a tool-schema dict, (3) an entry in `TOOL_FUNCTIONS` + the `TOOLS` list. All three, or the model can't call it.
- Tool functions take `db: Session` as their first parameter. `db` is injected by the loop and MUST NOT appear in the tool's `input_schema` — the model only supplies the other args.
- Return clean, reasoning-ready data (list of dicts with only useful fields) — not raw ORM rows, no `id`/timestamps unless relevant. Order results the way you'd want to read them (e.g. `get_bodyweight` returns oldest→newest so a trend reads left to right).
- Tool descriptions and parameter descriptions are PROMPTS — write them to tell the model what the tool does AND when to use it. Use enums for constrained args, and state defaults in the description.
- Every arg the model can omit needs a Python default AND must be left out of `required`.
- All tools are read-only for now. If you add a write tool, say so explicitly here and in the system prompt — the "read-only" assumption is load-bearing for how freely the model calls them.

### The agent loop (`run_agent`)
- Stateless and single-turn: one HTTP request → one fresh `messages` list → a string back. There is no conversation memory between `/agent/ask` calls. Don't assume the model remembers the last question.
- Loop shape: call `messages.create` → if `stop_reason != "tool_use"`, return the text → otherwise append the assistant turn, execute every `tool_use` block, append all `tool_result` blocks in a **single** user message, repeat.
- Each tool call opens its own `SessionLocal()` in a `try/finally` — the loop does not use FastAPI's `get_db` dependency, because it isn't inside the request's dependency graph.
- Tool results are passed as `str(result)`. Fine for the current small dicts; if a tool starts returning something large or nested, switch to `json.dumps`.
- `SYSTEM_PROMPT` is where the agent's voice and its "never guess at the data, pull the tool first" rules live. Prompt changes belong there, not smeared into tool descriptions.

### Frontend (`app/static/index.html`)
- One file on purpose: markup, CSS, and JS together, no bundler, no framework, no dependencies. Keep it that way unless asked.
- CSS lives in `:root` custom properties at the top (the terminal/amber palette) — use the existing vars, don't hardcode new colors.
- JS shape: a single `state` object mirroring the API collections, `loadAll()` to refetch everything, then `render*()` functions that rebuild their section from `state`. After any mutation, refetch and re-render rather than patching the DOM by hand.
- All network access goes through the `api()` helper and its `get/post/patch/del` wrappers — they handle the 204-no-body case and unwrap FastAPI's `detail` into an `Error`.
- Escape anything user-typed with `esc()` before putting it in `innerHTML`.
- The advisor panel just POSTs to `/agent/ask` and prints `res.response`.

## Known gaps (don't be surprised by these; don't "fix" them unasked)
- No auth, no rate limiting, no CORS config — it's a localhost app.
- No migrations, no tests.
- Deleting an `Exercise` that still has `ExerciseSet` rows raises a FK `IntegrityError` (500). Workouts cascade; exercises don't.
- Nothing stops `completed_page > total_page`, or a negative weight.
- The agent has no memory across requests and no write tools.

## Working style
- Match the existing patterns above rather than introducing new ones.
- Explain design decisions briefly ("why", not just "what") before/with the code.
- Never commit `.env` or secrets. Keep `.env.example` in sync when adding config.
- When adding a new tracked thing, the full slice is: model → schemas (×3) → router in `routes.py` → `create_tables` → a section in `index.html`, and only then an agent tool if the model would actually benefit from reading it.
