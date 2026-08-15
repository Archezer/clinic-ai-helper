# Project Guidance

## Goal

Build an educational but professionally structured AI clinic receptionist MVP
with FastAPI, OpenRouter, PostgreSQL, SQLAlchemy, Alembic, and Meta Messenger.
The core features are intent classification, FAQ answers, patient intake,
appointment booking, conversation history, and human handoff.

## Teaching style

- Speak to the user in Russian as an experienced engineer teaching a student.
- Keep all repository content in English.
- Give one small, coherent implementation step at a time.
- Present code in small chunks and explain each chunk before moving on.
- When reviewing user-written code, explain it first, then give the next step.
- Explain what each component does, why it exists, and how it connects to the
  request flow.
- Prefer real MVP code over disposable keyword-based examples.
- Do not overengineer.
- Diagnose errors before proposing the smallest correct fix.
- By default, provide code for the user to type. Edit implementation files only
  when the user explicitly asks.
- End every response with a bold Russian project-completion percentage.

## Engineering rules

- Use Python 3.12, modern typing, FastAPI, Pydantic v2, async SQLAlchemy, asyncpg,
  Alembic, pytest, and `uv`.
- Use OpenRouter through the OpenAI-compatible async SDK and Structured Outputs.
- Keep secrets in `.env`; maintain `.env.example`; never expose secrets.
- Let the LLM classify intent, but let deterministic Python code choose actions.
- Never give the LLM direct database or arbitrary SQL access.
- Keep API, orchestration, business rules, integrations, and persistence separate.
- Use one `AsyncSession` per request or unit of work.
- Convert provider failures into application exceptions and safe HTTP responses.
- Add isolated tests; normal tests must not call OpenRouter.
- Preserve user changes and avoid unrelated rewrites.

## Medical safety

- Never diagnose, assess symptoms, prescribe medicine, or recommend treatment.
- Route medical questions and explicit human requests to a human-controlled flow.
- Do not claim the MVP is suitable for real clinical use.

## Verification

Use the narrowest relevant check, then run the full suite when practical:

