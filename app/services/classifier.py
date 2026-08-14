from openai import AsyncOpenAI, OpenAIError
from pydantic import ValidationError

from app.services.exceptions import ClassificationUnavailableError
from app.schemas.classification import MessageClassification


SYSTEM_PROMPT = """
You classify messages sent to a medical clinic receptionist.

Choose exactly one primary user intent:

- greeting: a greeting without another substantive request;
- book_appointment: a request to book, reschedule, cancel, or discuss an
  appointment;
- clinic_faq: a question about clinic fees, location, opening hours, services,
  or policies;
- medical_question: a request for a diagnosis, symptom assessment, treatment,
  or medication recommendation;
- human_request: an explicit request to speak with a person;
- unknown: a message that does not fit any category above.

Do not answer the user and do not provide medical advice. Return only the
classification result.
""".strip()


class MessageClassifier:
    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self._client = client
        self._model = model

    async def classify(self, message: str) -> MessageClassification:
        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "message_classification",
                        "strict": True,
                        "schema": MessageClassification.model_json_schema(),
                    },
                },
                extra_body={
                    "provider": {
                        "require_parameters": True,
                    },
                },
            )

            content = completion.choices[0].message.content

            if content is None:
                raise RuntimeError("OpenRouter returned an empty response")

            return MessageClassification.model_validate_json(content)
        except ClassificationUnavailableError:
            raise

        except (OpenAIError, ValidationError, IndexError) as error:
            raise ClassificationUnavailableError(
                'Message classification failed'
            ) from error