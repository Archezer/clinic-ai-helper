# Clinic AI Helper

**A production-minded AI receptionist backend built around a simple rule: the LLM can understand language, but it does not control the system.**

Clinic AI Helper is an end-to-end FastAPI application that combines **LLM intent classification, deterministic action routing, PDF-backed RAG, PostgreSQL conversation state, Meta Messenger integration, human handoff, and appointment intake**.

Unlike a typical chatbot wrapper, the LLM never receives database access, never generates SQL, and never decides which application actions to execute. It is treated as a probabilistic component inside a deterministic backend.

## Live demo

- **Web app:** [archezer.github.io/clinic-ai-helper](https://archezer.github.io/clinic-ai-helper/)
- **Swagger API:** [clinic-ai-helper-api.onrender.com/docs](https://clinic-ai-helper-api.onrender.com/docs)
- **Health check:** [clinic-ai-helper-api.onrender.com/health](https://clinic-ai-helper-api.onrender.com/health)
- **Deployment branch:** [`demo-deploy`](https://github.com/Archezer/clinic-ai-helper/tree/demo-deploy)

> This is an educational engineering project, not a production clinical system. It does not diagnose patients, assess symptoms, recommend treatment, prescribe medication, or automatically confirm appointments.

---

## Why this project is non-trivial

The interesting part is not calling an LLM API. The project is built around the engineering problems that appear when an AI component becomes part of a stateful backend:

- **deterministic routing** — the LLM classifies intent, Python decides what the application actually does;
- **grounded RAG** — generated answers are limited to retrieved clinic documentation;
- **safe fallback behavior** — unsupported questions are escalated instead of hallucinated;
- **conversation state** — PostgreSQL stores conversations, messages, appointments, FAQs, and handoff state;
- **idempotent webhook processing** — repeated Messenger message IDs are not processed twice;
- **provider isolation** — Meta Messenger and OpenRouter are hidden behind testable application boundaries;
- **human handoff** — the bot stops answering once an operator takes control;
- **async persistence** — request-scoped SQLAlchemy sessions with PostgreSQL and Alembic migrations;
- **isolated tests** — normal test runs make no real OpenRouter, Meta, or PostgreSQL calls;
- **deployable system** — Docker backend on Render with a separate static frontend on GitHub Pages.

---

## Architecture

```text
                  ┌─────────────────────┐
                  │   Meta Messenger    │
                  │    or Web Demo      │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │      FastAPI        │
                  │ integration layer   │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │     ChatService     │
                  │   orchestration     │
                  └──────────┬──────────┘
                             │
                 ┌───────────▼───────────┐
                 │    LLM classifier     │
                 │ structured intent only│
                 └───────────┬───────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │ Deterministic router  │
                 └───────────┬───────────┘
                             │
       ┌─────────────────────┼──────────────────────┐
       │                     │                      │
       ▼                     ▼                      ▼
   PDF RAG / FAQ        Appointment flow       Human handoff
       │                     │                      │
       └─────────────────────┼──────────────────────┘
                             ▼
                      Repositories
                             │
                             ▼
                        PostgreSQL
```

### The important boundary

The LLM has two responsibilities:

1. classify the user's intent using Structured Outputs;
2. generate an answer from retrieved document excerpts when RAG has sufficient evidence.

It **does not**:

- execute SQL;
- call repositories;
- choose application actions;
- confirm appointments;
- bypass safety rules;
- decide whether operator state should be overwritten.

Those decisions remain deterministic application logic.

---

## Core features

### AI and routing

- OpenRouter intent classification with Structured Outputs
- deterministic Python action routing
- PDF-backed RAG
- BM25-style local retrieval
- grounded answer generation
- approved database FAQ fallback
- explicit unsupported-answer handling

### Backend

- FastAPI
- async SQLAlchemy
- PostgreSQL
- request-scoped database sessions
- Alembic migrations
- Pydantic configuration and schemas

### Messenger integration

- Meta webhook verification
- HMAC request-signature validation
- idempotent handling of duplicate Messenger message IDs
- filtering of echoes, receipts, unsupported events, and non-text messages
- Messenger Send API adapter behind a testable protocol
- fake Messenger implementation for local development

### Conversation workflows

- persisted conversation and message history
- patient name and phone collection
- appointment request intake
- `requested`, `confirmed`, and `cancelled` appointment states
- human handoff queue
- operator conversation history
- operator reply and conversation close operations

### Delivery

- Docker
- Docker Compose for local PostgreSQL
- Render deployment
- GitHub Pages frontend
- GitHub Actions deployment workflow
- environment-based configuration

---

## RAG pipeline

Administrative questions are answered using a controlled retrieval pipeline:

```text
PDF
 │
 ▼
pypdf text extraction
 │
 ▼
page-aware chunks
 │
 ▼
BM25-style retrieval
 │
 ▼
top-k relevant chunks
 │
 ▼
LLM grounded generation
 │
 ▼
supported / unsupported decision
 │
 ▼
answer + deterministic source metadata
```

The generator receives only the user's question and retrieved context.

If retrieval cannot provide enough evidence, the application falls back to an approved FAQ stored in PostgreSQL.

If neither source can support an answer, the conversation is sent to **human handoff** rather than producing an invented clinic answer.

---

## Appointment flow

The assistant collects:

1. patient's full name;
2. callback phone number;
3. preferred date and time.

The application creates an appointment request with:

```text
status = requested
```

The assistant never claims that the requested slot has been booked.

A staff member must later explicitly change the request to:

```text
confirmed
```

or:

```text
cancelled
```

through the operator API.

---

## Human handoff

Certain conversations should not remain under automated control.

Medical questions and explicit requests for a human operator move the conversation into:

```text
needs_human
```

Once handed off:

- incoming messages are still persisted;
- the bot no longer responds over the operator;
- staff can inspect history;
- staff can reply;
- staff can close the handoff.

This state transition is controlled by application logic, not by free-form LLM tool calls.

---

## Project structure

```text
app/
├── api/                # HTTP routes
├── core/               # configuration and shared infrastructure
├── integrations/       # Meta Messenger / external providers
├── models/             # SQLAlchemy models
├── repositories/       # persistence layer
├── schemas/            # Pydantic schemas
├── services/           # application and domain logic
├── dependencies.py     # dependency wiring
└── main.py             # FastAPI application

migrations/             # Alembic migrations
tests/                  # unit and API tests
frontend/               # standalone web demo
Dockerfile
compose.yaml
render.yaml
pyproject.toml
```

---

## API

### System

```http
GET /health
```

### Development chat API

```http
POST /chat/classify
POST /chat/process
```

### Messenger

```http
GET  /webhooks/messenger
POST /webhooks/messenger
```

### Operator API

Operator routes require:

```http
X-Admin-Token: <ADMIN_API_TOKEN>
```

Available operations:

```http
GET   /admin/handoffs
GET   /admin/conversations/{conversation_id}/messages
POST  /admin/conversations/{conversation_id}/reply
POST  /admin/conversations/{conversation_id}/close

GET   /admin/faqs
POST  /admin/faqs

GET   /admin/appointments
PATCH /admin/appointments/{appointment_id}
```

---

## Local Messenger simulator

The real Meta integration can be replaced with a fake transport:

```dotenv
MESSENGER_MODE=fake
```

Then a local message can be sent through:

```http
POST /debug/messenger/messages
```

Example:

```json
{
  "sender_id": "demo-user",
  "text": "How should I prepare for an ultrasound visit?"
}
```

This executes the real application pipeline:

```text
message
→ intent classification
→ routing
→ RAG / FAQ / booking / handoff
→ persistence
→ outgoing Messenger adapter
```

but captures the outgoing message locally instead of calling Meta.

This makes the complete workflow testable without external Messenger credentials.

---

## Testing

Run:

```bash
uv run pytest -q
```

The suite covers application services, repositories, APIs, Messenger behavior, booking, handoff, FAQ logic and provider integrations.

External services are replaced with:

- stubs;
- `AsyncMock`;
- `httpx.MockTransport`;
- fake Messenger adapters.

Normal tests do **not** call:

- OpenRouter;
- Meta APIs;
- a live PostgreSQL instance.

---

## Local development

### Requirements

- Python 3.12
- `uv`
- Docker
- PostgreSQL 17

Create the environment file:

```bash
cp .env.example .env
```

Install dependencies:

```bash
uv sync
```

Start PostgreSQL:

```bash
docker compose up -d db
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Start FastAPI:

```bash
uv run uvicorn app.main:app --reload
```

Available locally:

```text
API        http://127.0.0.1:8000
Swagger    http://127.0.0.1:8000/docs
Health     http://127.0.0.1:8000/health
```

---

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

MESSENGER_MODE=fake

ADMIN_API_TOKEN=
```

Secrets belong in environment variables and must never be committed to the repository or frontend bundle.

---

## Deployment

### Backend

The FastAPI backend is deployed on Render:

```text
https://clinic-ai-helper-api.onrender.com
```

The repository includes:

- `Dockerfile`
- `render.yaml`

Render creates the API service and PostgreSQL database and runs Alembic migrations before starting Uvicorn.

### Frontend

The static frontend is deployed with GitHub Actions to:

```text
https://archezer.github.io/clinic-ai-helper/
```

The browser communicates with the Render API over HTTPS.

The OpenRouter API key exists only on the backend.

---

## Current production gaps

This repository demonstrates the architecture but deliberately does not claim production readiness.

Important remaining gaps include:

- webhook work currently happens synchronously instead of through a durable queue;
- distributed message delivery should use a transactional outbox or equivalent mechanism;
- concurrent first-message creation needs stronger conflict recovery;
- admin authentication uses a shared token rather than staff identities and RBAC;
- appointment requests are not connected to a real scheduling provider;
- attachments and Messenger postbacks are not implemented;
- observability and alerting are minimal;
- backups and retention policies are not defined;
- encryption and privacy requirements require formal review;
- real patient data would require a dedicated clinical, legal, and security assessment.

---

## What this project demonstrates

The goal of Clinic AI Helper is not to demonstrate that an LLM can answer messages.

It demonstrates how an LLM can be integrated into a **stateful backend while keeping critical application behavior deterministic, testable, observable, and replaceable**.