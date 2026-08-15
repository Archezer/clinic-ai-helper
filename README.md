# Clinic AI Receptionist

An educational FastAPI MVP for a clinic receptionist connected to Meta
Messenger. It classifies incoming messages with OpenRouter, keeps conversation
history, answers only approved FAQs, collects appointment requests, and routes
medical or operator requests to a human-controlled flow.

This project is not suitable for real clinical use. It does not diagnose,
assess symptoms, recommend treatment, prescribe medication, or confirm medical
appointments without staff review.

## Features

- Meta Messenger webhook verification and HMAC signature validation
- idempotent handling of repeated Messenger message IDs
- OpenRouter intent classification with Structured Outputs
- deterministic Python action routing
- PostgreSQL conversation and message history
- PDF-backed RAG answers with deterministic retrieval and grounded generation
- approved FAQ storage as a fallback knowledge source
- patient name and phone intake
- appointment request collection without false slot confirmation
- human handoff queue, history, reply, and close operations
- Messenger Send API adapter behind a testable protocol
- request-scoped async SQLAlchemy sessions
- Alembic migrations and isolated tests with no real provider calls

## Architecture

```text
Meta webhook
    -> FastAPI integration layer
    -> ChatService orchestration
    -> intent classifier
    -> deterministic router
    -> PDF RAG / FAQ / booking / handoff services
    -> repositories
    -> PostgreSQL
    -> Messenger Send API
```

The LLM classifies intent and composes grounded answers from retrieved PDF
excerpts. It never receives database access and never chooses SQL or
application actions.

## Local development

Requirements:

- Python 3.12
- uv
- Docker Desktop or another PostgreSQL 17 installation

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Fill at least the OpenRouter and database settings. Meta values can remain
empty when running tests.

Install dependencies:

```powershell
uv sync
```

Start PostgreSQL:

```powershell
docker compose up -d db
```

Apply migrations:

```powershell
uv run alembic upgrade head
```

Start the API:

```powershell
uv run uvicorn app.main:app --reload
```

Available locally:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- health check: http://127.0.0.1:8000/health

## Configuration

```dotenv
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
RAG_DOCUMENT_PATH=output/pdf/clinic_faq_rag_demo.pdf
RAG_TOP_K=4
RAG_MIN_SCORE=0.12
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/clinic_bot

META_VERIFY_TOKEN=
META_APP_SECRET=
META_PAGE_ACCESS_TOKEN=
META_GRAPH_BASE_URL=https://graph.facebook.com
META_GRAPH_API_VERSION=v23.0

ADMIN_API_TOKEN=
```

Use the Graph API version supported by the Meta application when credentials
become available. Never commit `.env` or real provider tokens.

## Main endpoints

### System and development

- `GET /health`
- `POST /chat/classify`
- `POST /chat/process`

The `/chat` routes are useful for development. The Messenger webhook is the
intended production entry point.

### Messenger

- `GET /webhooks/messenger` verifies the callback URL
- `POST /webhooks/messenger` validates and processes signed events

Delivery receipts, read receipts, echoes, and unsupported non-text events are
acknowledged but ignored.

### Operator API

All operator routes require:

```http
X-Admin-Token: <ADMIN_API_TOKEN>
```

- `GET /admin/handoffs`
- `GET /admin/conversations/{conversation_id}/messages`
- `POST /admin/conversations/{conversation_id}/reply`
- `POST /admin/conversations/{conversation_id}/close`
- `GET /admin/faqs`
- `POST /admin/faqs`
- `GET /admin/appointments`
- `PATCH /admin/appointments/{appointment_id}`

FAQ answers should be added only after clinic staff approve their content.

## RAG knowledge answers

Administrative FAQ messages first use the configured PDF knowledge base:

1. `pypdf` extracts text and divides it into page-aware chunks;
2. a local BM25-style retriever selects the most relevant chunks;
3. OpenRouter receives only the question and retrieved context;
4. Structured Outputs requires an explicit supported/unsupported decision;
5. the application appends deterministic document, page, and service labels.

If retrieval or generation cannot support an answer, the service falls back to
an approved database FAQ. If neither source answers the question, the existing
human handoff flow is used. Normal tests mock generation and never call
OpenRouter.

## Appointment flow

The assistant collects:

1. full name;
2. callback phone number;
3. preferred date and time as text.

It creates an appointment with status `requested`. It explicitly tells the
patient that staff must confirm the time. Operators can later mark the request
as `confirmed` or `cancelled` through the admin API.

## Medical safety

Messages classified as medical questions and explicit requests for a person
immediately set the conversation status to `needs_human`. Once handed off, the
bot stores follow-up messages but does not reply over the human operator.

If an FAQ has no approved matching answer, it also enters human handoff instead
of inventing clinic information.

## Tests

Run the complete suite:

```powershell
uv run pytest -q
```

Normal tests use stubs, `AsyncMock`, and `httpx.MockTransport`. They do not call
OpenRouter, Meta, or a live PostgreSQL database.

## Known production gaps

- webhook processing is synchronous; production should use a durable queue
- distributed delivery would benefit from a transactional outbox
- concurrent first messages need stronger conflict recovery around unique IDs
- admin authentication is a shared token, not staff identity and role control
- appointment requests are not connected to a real scheduling system
- attachments and postbacks are not implemented
- observability, retention policies, encryption review, backups, and a formal
  clinical/privacy assessment are required before handling real patient data
