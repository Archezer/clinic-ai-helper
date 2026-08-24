from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SentMessage:
    recipient_id: str
    text: str


class FakeMessageSender:
    def __init__(self) -> None:
        self.messages: list[SentMessage] = []

    async def send_text(
        self,
        recipient_id: str,
        text: str,
    ) -> None:
        self.messages.append(
            SentMessage(
                recipient_id=recipient_id,
                text=text,
            )
        )
