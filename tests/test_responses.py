import pytest

from app.schemas.routing import ChatAction
from app.services.responses import ResponseComposer


@pytest.mark.parametrize("action", list(ChatAction))
def test_composes_non_empty_response_for_every_action(
    action: ChatAction,
) -> None:
    response = ResponseComposer().compose(action)

    assert response
    assert len(response) <= 1000


def test_handoff_response_does_not_give_medical_advice() -> None:
    response = ResponseComposer().compose(
        ChatAction.HAND_OFF_TO_HUMAN,
    )

    assert "cannot assess symptoms" in response
    assert "staff member" in response
