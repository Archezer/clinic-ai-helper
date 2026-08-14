from app.schemas.routing import RoutingDecision
from app.services.router import MessageRouter
from app.services.classifier import MessageClassifier


class ChatService:
    def __init__(
        self, 
        classifier: MessageClassifier,
        router: MessageRouter
    ) -> None:
        self._classifier = classifier
        self._router = router

    async def process_message(
        self,
        message: str,
    ) -> RoutingDecision:
        classification = await self._classifier.classify(message)

        return self._router.route(classification)