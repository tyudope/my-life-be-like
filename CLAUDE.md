# My Life Be Like — Project Guide

A personal life-tracking app (books, bodyweight, workouts) with a Claude-powered
agent that reads the user's data via tool use and gives recommendations.

## Stack
- Python 3.11, FastAPI, SQLAlchemy 2.0 (Mapped/mapped_column style), Pydantic v2
- PostgreSQL (via Docker Compose), psycopg driver
- Anthropic Claude API (tool use)
- Config via pydantic-settings; secrets in `.env` (gitignored), keys in `.env.example`

## Project structure
- `app/models.py` — all SQLAlchemy tables
- `app/schemas.py` — all Pydantic schemas
- `app/routes.py` — CRUD routers (one APIRouter per domain, combined into one)
- `app/database.py` — engine, SessionLocal, get_db, Base
- `app/config.py` — Settings
- `app/agent/` — the AI agent
  - `tools.py` — tool functions + their tool-schema dicts
  - `agent.py` — the run_agent loop (client, TOOLS list, TOOL_FUNCTIONS dispatch dict)
  - `routes.py` — the /agent endpoint

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
- Create: build model with `X(**payload.model_dump())` → add → commit → refresh.
- Update (PATCH): fetch → 404 if None → `payload.model_dump(exclude_unset=True)` → setattr each → commit → refresh.
- Delete: fetch → 404 if None → delete → commit → 204, no body.
- Get-one: `db.get(Model, id)`, raise `HTTPException(404)` if None.
- Routes are `def` (sync), not `async` — the Claude client is synchronous.

### Agent tools — THE most important conventions
- A tool FETCHES FACTS or takes an action. A tool NEVER does the reasoning/judgment — that is the model's job. (e.g. a tool returns workout history; the MODEL decides whether to add weight. Do NOT put "should I add weight" logic in Python.)
- Each tool = (1) a query function, (2) a tool-schema dict, (3) an entry in `TOOL_FUNCTIONS`.
- Tool functions take `db: Session` as their first parameter. `db` is injected by the loop and MUST NOT appear in the tool's input_schema — the model only supplies the other args.
- Return clean, reasoning-ready data (list of dicts with only useful fields) — not raw ORM rows, no `id`/timestamps unless relevant.
- Tool descriptions and parameter descriptions are PROMPTS — write them to tell the model what the tool does AND when to use it. Use enums for constrained args.
- All tools are read-only for now.

## Working style
- Match the existing patterns above rather than introducing new ones.
- Explain design decisions briefly ("why", not just "what") before/with the code.
- Never commit `.env` or secrets. Keep `.env.example` in sync when adding config.