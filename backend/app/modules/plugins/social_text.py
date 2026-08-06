import unicodedata


def normalize_social_text(value: str) -> str:
    """Preserve Spanish text consistently across JSON, PostgreSQL and Meta APIs."""
    return unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
