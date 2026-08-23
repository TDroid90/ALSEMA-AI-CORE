import re

from app.modules.creative.schemas import CreativeContent

PRICE_PATTERNS = (
    ("currency_symbol", re.compile(r"(?:^|\s)[$€£](?:\s|\d)")),
    ("currency_code", re.compile(r"\b(?:usd|ars|eur)\b", re.IGNORECASE)),
    ("price", re.compile(r"\b(?:precio|oferta|descuento)\b", re.IGNORECASE)),
    ("installments", re.compile(r"\b(?:cuota|cuotas|financiaci[oó]n)\b", re.IGNORECASE)),
    ("percentage", re.compile(r"\d\s*%")),
)


def validate_creative_policy(content: CreativeContent) -> list[str]:
    if content.brand != "cometag":
        return []
    text = " ".join([content.title, content.short_title or "", content.description, *content.specs])
    errors = [
        f"Contenido de precio prohibido: {name}"
        for name, pattern in PRICE_PATTERNS
        if pattern.search(text)
    ]
    if content.cta != "Ver producto":
        errors.append("El CTA de Cometa G debe ser 'Ver producto'")
    return errors
