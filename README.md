# Clinic AI Receptionist

An educational AI chatbot for clinic FAQs, patient intake, appointment booking,
and escalation of complex conversations to a human.

## Local development

```powershell
uv sync
uv run uvicorn app.main:app --reload
```

After starting the application:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health
