from app.api.creative import router
from app.modules.identity.rbac import PERMISSIONS


def test_creative_api_contract_is_registered() -> None:
    methods_by_path: dict[str, set[str]] = {}
    for route in router.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods_by_path.setdefault(route.path, set()).update(route.methods)
    assert "GET" in methods_by_path["/api/v1/creative/brands"]
    assert "GET" in methods_by_path["/api/v1/creative/catalog"]
    assert "POST" in methods_by_path["/api/v1/creative/catalog/import"]
    assert "POST" in methods_by_path["/api/v1/creative/catalog/google-sheets/sync"]
    assert "POST" in methods_by_path["/api/v1/creative/catalog/{item_id}/prepare"]
    assert "POST" in methods_by_path["/api/v1/creative/jobs"]
    assert "POST" in methods_by_path["/api/v1/creative/jobs/{job_id}/decision"]
    assert "GET" in methods_by_path["/api/v1/creative/assets/{asset_id}/content"]
    assert "POST" in methods_by_path["/api/v1/creative/imports/creativosur"]


def test_creative_permissions_are_seeded() -> None:
    required = {
        "creative.view",
        "creative.create",
        "creative.edit",
        "creative.generate",
        "creative.approve",
        "creative.export",
        "creative.manage_templates",
        "creative.manage_brands",
        "creative.manage_catalogs",
        "creative.manage_providers",
    }
    assert not required.difference(PERMISSIONS)
