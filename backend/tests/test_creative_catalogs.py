import json

import pytest

from app.modules.creative.catalogs import normalize_catalog_row, parse_catalog_file


def test_csv_adapter_preserves_facts_without_prices() -> None:
    rows = parse_catalog_file(
        "id,nombre,categoria,atributos,precio\nsku-1,Auriculares,Audio,Bluetooth|Micrófono,999\n".encode(),
        "productos.csv",
        "cometag",
    )
    assert rows[0]["title"] == "Auriculares"
    assert rows[0]["specs"] == ["Bluetooth", "Micrófono"]
    assert "precio" not in rows[0]


def test_json_adapter_accepts_canonical_catalog() -> None:
    raw = json.dumps([{"id": "sku-2", "title": "Teclado mecánico", "specs": ["RGB"]}]).encode()
    assert parse_catalog_file(raw, "productos.json", "cometag")[0]["id"] == "sku-2"


def test_catalog_adapter_requires_stable_identity() -> None:
    with pytest.raises(ValueError):
        normalize_catalog_row({"nombre": "Sin identidad"}, "cometag", "manual")
