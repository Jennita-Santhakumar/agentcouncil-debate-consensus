# Multi-Agent Debate System

> **Maintained by [Jennita S](https://github.com/Jennita-Santhakumar)** · [LinkedIn](https://linkedin.com/in/jennitas) · jennitasanthakumar0@gmail.com

Two LangChain agents (Pro and Con) debate a topic over N rounds. A third
Evaluator agent scores every round on four sub-criteria as it happens. FastAPI
orchestrates the debate and streams each round over a WebSocket the instant
it finishes — the client never blocks until the whole debate is done. A React
UI shows arguments, a live scoreboard, and the final winner. Everything is
persisted in Postgres.

## Architecture

```
                         ┌─────────────────────────────┐
                         │           Browser            │
                         │  React + TS (DebateArena)    │
                         └───────────┬───────────┬──────┘
                                     │ REST      │ WebSocket
                                     │ POST/GET  │ /ws/debate/{id}
                                     ▼           ▼
                         ┌─────────────────────────────┐
                         │      FastAPI (backend)       │
                         │  ┌─────────────────────────┐ │
                         │  │   DebateOrchestrator     │ │
                         │  │  ┌───────┐   ┌────────┐  │ │
                         │  │  │  Pro  │   │  Con   │  │ │      ┌───────────────┐
                         │  │  │ agent │   │ agent  │  │ │◄────►│  LLM provider  │
                         │  │  └───┬───┘   └───┬────┘  │ │      │ Ollama (free)  │
                         │  │      │  round N  │       │ │      │  or Anthropic  │
                         │  │      ▼           ▼       │ │      └───────────────┘
                         │  │  ┌─────────────────────┐ │ │
                         │  │  │  Evaluator (scores)  │ │ │
                         │  │  └──────────┬──────────┘ │ │
                         │  └─────────────┼────────────┘ │
                         │   on_round_complete callback   │
                         │        │                │      │
                         │        ▼                ▼      │
                         │  ConnectionManager   AsyncSession│
                         │  (WS broadcast)      (persist)  │
                         └────────┬────────────────┬───────┘
                                  │                 │
                          WS: round_complete   ┌─────────────┐
                          debate_complete      │  Postgres    │
                                               │ debates,     │
                                               │ debate_rounds│
                                               └─────────────┘

     Pro/Con agents also call a module-level `search_evidence` tool
     (LangChain @tool → DuckDuckGo via the free `ddgs` package, no API key).
```

## Setup

### Backend (local, no Docker)

```bash
cd backend
# Needs Python 3.11
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt -r requirements-dev.txt

cp ../.env.example ../.env   # or backend/.env, both are read
# make sure a local Postgres is reachable at DATABASE_URL, or use docker compose up postgres

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Run the test suite (uses `testcontainers` to spin up a throwaway Postgres and
a `fake_llm.py` mock, so it needs Docker but not Ollama/Anthropic):

```bash
pytest tests/ -v
```

### Frontend (local, no Docker)

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL / VITE_WS_BASE_URL
npm run dev            # http://localhost:5173
```

### Full stack via Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

- Postgres: `localhost:5512`
- Backend: `http://localhost:8100`
- Frontend: `http://localhost:5300`

The backend defaults to `LLM_PROVIDER=ollama`. If you run Ollama natively on
Windows/macOS (not in a container), the backend reaches it via
`http://host.docker.internal:11434` — make sure Ollama is listening on
`0.0.0.0:11434` (not just `127.0.0.1`), and that `ollama pull llama3.2:3b` has
been run. To use Claude instead, set `LLM_PROVIDER=anthropic` and
`ANTHROPIC_API_KEY` in `.env`.

## API Reference

### `POST /api/v1/debates`

Starts a debate in the background and returns immediately.

```json
// request
{ "topic": "Should AI development be paused for safety research?", "num_rounds": 3 }

// 201 response
{ "debate_id": "20829e2b-9837-4075-a0dc-6ee468ce18b7" }
```

### `GET /api/v1/debates`

List debates, newest first (summary — no round detail).

```json
[
  {
    "id": "20829e2b-...",
    "topic": "...",
    "num_rounds": 3,
    "status": "completed",
    "pro_score": 12.0,
    "con_score": 13.0,
    "winner": "con",
    "created_at": "2026-09-22T10:00:00Z"
  }
]
```

### `GET /api/v1/debates/{id}`

Full debate detail including every persisted round.

### `WS /ws/debate/{id}`

Connect right after creating a debate to receive round-by-round updates.
No client → server messages are required; the socket is receive-only.

```json
// after each round
{
  "type": "round_complete",
  "debate_id": "...",
  "round_number": 1,
  "pro_argument": "...",
  "pro_score_breakdown": {
    "logical_strength": 2.0, "evidence_quality": 2.0,
    "clarity": 1.0, "counterargument_handling": 0.5,
    "feedback": "...", "total": 5.5
  },
  "con_argument": "...",
  "con_score_breakdown": { "...": "..." },
  "running_pro_score": 5.5,
  "running_con_score": 6.5
}

// once, at the end
{ "type": "debate_complete", "debate_id": "...", "winner": "con", "pro_score": 12.0, "con_score": 13.0 }

// on any orchestration failure
{ "type": "debate_failed", "debate_id": "...", "error": "..." }
```

## Design Decisions & Trade-offs

**Ollama-default, Claude-optional.** `LLM_PROVIDER=ollama` with
`llama3.2:3b` is the default so the whole stack runs for $0 with no API key.
Honest caveat: a 3B local model's debate arguments and evaluator scoring are
noticeably weaker than a frontier model — verified live during development,
llama3.2:3b tends to be repetitive across rounds, occasionally echoes its own
instructions ("Here is a 150-250 word persuasive argument for the Con
side...") instead of just writing the argument, and its self-scoring clusters
tightly (`clarity` almost always lands at 1.0/2, `feedback` sometimes comes
back empty). Setting `LLM_PROVIDER=anthropic` with an API key swaps in
`claude-3-5-haiku-latest` for materially better argument quality and scoring
discrimination, at a small per-debate cost.

**Real DuckDuckGo search, not the PRD's mock.** The PRD's evidence tool was
an explicitly labeled stub returning canned text. `app/agents/tools.py`
performs a real, free web search via the `ddgs` package (no API key), with a
try/except fallback so a network hiccup or rate limit degrades gracefully
(the debater is told no citation was available) instead of crashing the
round.

**LangChain API fixes vs. the PRD's reference code.** The PRD defines
`@tool`-decorated *methods* bound to `self`; LangChain's `@tool` decorator
builds a `StructuredTool` from a plain function signature and doesn't work
correctly on a bound method (the injected `self` parameter corrupts the
tool's schema). This implementation uses module-level functions instead. The
PRD also calls the removed `AgentExecutor.from_agent_and_tools(...)`
classmethod; this implementation uses the current Runnable-based
`create_tool_calling_agent(...)` + `AgentExecutor(agent=agent, tools=tools)`.

**Structured, crash-resistant evaluator scoring vs. the PRD's `float()`
parse.** The PRD reference parses a raw LLM response with a bare
`float(response.content)`, which throws on almost any real model output.
`EvaluatorChain` first tries `llm.with_structured_output(RoundScore)`
(reliable on capable models); if that's unsupported or fails, it falls back
to a regex-based parser (`_fallback_parse_score`) that extracts each of the
four sub-scores independently, clamps them to their valid ranges, and — if
literally nothing parseable comes back — returns a conservative mid-range
score instead of raising. A single malformed model response never takes down
a debate round.

**Real round-by-round streaming and persistence vs. the PRD's unwired
synchronous version.** `DebateOrchestrator.run_debate` accepts an
`on_round_complete` async callback invoked immediately after each round's Pro
argument, Con argument, and both scores are ready — not after the whole
debate finishes. `routes.py` wires that callback to insert a `debate_rounds`
row, update the running `debates.pro_score`/`con_score`, commit, and then
broadcast the same round over the `ConnectionManager`'s WebSocket fan-out, in
that order, so a client connecting mid-debate and a client reading straight
from Postgres never disagree.

**No Redis.** A single debate's orchestration lives entirely inside one
FastAPI background task in one process, and `ConnectionManager` is a plain
in-memory `dict[str, list[WebSocket]]`. That's sufficient fan-out for
everyone watching a given debate; it would only need to become a Redis
pub/sub if the API were horizontally scaled across multiple processes/nodes.

## Ports

| Service    | Port |
|------------|------|
| Postgres   | 5512 |
| Backend    | 8100 |
| Frontend   | 5300 |

## Credits

Developed by Kabilesh Rajaselvan with contributions from Jennita S.
