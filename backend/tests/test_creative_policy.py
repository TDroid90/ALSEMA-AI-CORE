from app.modules.creative.policy import validate_creative_policy
from app.modules.creative.schemas import CreativeContent


def _content(**overrides: object) -> CreativeContent:
    values: dict[str, object] = {
        "id": "sku-1",
        "brand": "cometag",
        "title": "Auriculares inalámbricos",
        "description": "Sonido claro para jugar y trabajar.",
        "specs": ["Conexión Bluetooth", "Micrófono integrado"],
        "cta": "Ver producto",
    }
    values.update(overrides)
    return CreativeContent.model_validate(values)


def test_cometag_copy_accepts_spanish_accents() -> None:
    assert validate_creative_policy(_content()) == []


def test_cometag_copy_rejects_prices_and_discounts() -> None:
    errors = validate_creative_policy(
        _content(title="Auriculares 30% OFF", description="Ahora por $ 25.000")
    )
    assert errors
    assert any("precio" in error.casefold() or "descuento" in error.casefold() for error in errors)


def test_cometag_copy_rejects_unapproved_cta() -> None:
    assert validate_creative_policy(_content(cta="Comprar ahora"))
