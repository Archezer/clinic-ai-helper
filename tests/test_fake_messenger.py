import asyncio

from app.integrations.fake_messenger import FakeMessageSender, SentMessage


def test_records_outgoing_message_without_external_request() -> None:
    sender = FakeMessageSender()

    asyncio.run(
        sender.send_text(
            recipient_id="demo-user",
            text="Hello from the fake Messenger API",
        )
    )

    assert sender.messages == [
        SentMessage(
            recipient_id="demo-user",
            text="Hello from the fake Messenger API",
        )
    ]
