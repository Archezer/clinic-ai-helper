class ClassificationUnavailableError(RuntimeError):
    """Raised when message classification cannot be completed."""


class DuplicateMessageError(RuntimeError):
    """Raised when a provider message has already been processed."""


class MessageDeliveryError(RuntimeError):
    """Raised when an outgoing message cannot be delivered."""


class KnowledgeGenerationUnavailableError(RuntimeError):
    """Raised when a grounded RAG answer cannot be generated."""
