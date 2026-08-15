import hashlib
import hmac


SIGNATURE_PREFIX = "sha256="


def is_valid_signature(
    body: bytes,
    signature: str | None,
    app_secret: str,
) -> bool:
    if signature is None or not signature.startswith(SIGNATURE_PREFIX):
        return False

    expected_signature = SIGNATURE_PREFIX + hmac.new(
        app_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)
