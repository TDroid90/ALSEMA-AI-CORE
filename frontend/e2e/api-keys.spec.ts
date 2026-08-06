import { expect, test } from "@playwright/test";

test("creates an API key and shows the full secret only once", async ({ page }) => {
  const createdAt = "2026-08-06T12:00:00Z";
  const fullKey = "alsema_sk_test_secret_visible_once_12345678901234567890";
  let keys: object[] = [];

  await page.route("http://localhost:8000/api/v1/**", async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === "/api/v1/setup/status") return route.fulfill({ json: { setup_required: false } });
    if (path === "/api/v1/auth/login") return route.fulfill({ json: { access_token: "test-session" } });
    if (path === "/api/v1/providers/ollama/models") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/conversations") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/models/sync") return route.fulfill({ json: {} });
    if (path === "/api/v1/models") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/api-keys" && request.method() === "GET") {
      return route.fulfill({ json: { items: keys, available_scopes: ["agents:read", "agents:execute", "models:read", "tasks:read"] } });
    }
    if (path === "/api/v1/api-keys" && request.method() === "POST") {
      keys = [{ id: "33333333-3333-3333-3333-333333333333", name: "instanews-rewriter", key_prefix: "alsema_sk_test_secre", user_id: "11111111-1111-1111-1111-111111111111", scopes: ["agents:read", "agents:execute"], enabled: true, created_at: createdAt }];
      return route.fulfill({ status: 201, json: { ...keys[0], api_key: fullKey } });
    }
    return route.fulfill({ status: 404, json: { detail: `Unhandled test route ${path}` } });
  });

  await page.goto("/");
  await page.getByLabel("Correo").fill("admin@example.test");
  await page.getByLabel("Contraseña").fill("test-password");
  await page.getByRole("button", { name: "Ingresar" }).click();
  await page.getByRole("button", { name: "Configuración" }).click();

  await expect(page).toHaveURL(/#\/settings\/api-keys$/);
  await page.getByLabel("Nombre").fill("instanews-rewriter");
  await page.getByLabel("agents:execute").check();
  await page.getByRole("button", { name: "Crear API Key" }).click();

  await expect(page.getByRole("dialog", { name: "API Key creada" })).toBeVisible();
  await expect(page.getByLabel("API Key completa")).toHaveValue(fullKey);
  await expect(page.getByText("alsema_sk_test_secre••••••••")).toBeVisible();
  await page.getByRole("button", { name: "Ya la guardé" }).click();
  await expect(page.getByLabel("API Key completa")).toHaveCount(0);
  await expect(page.locator("body")).not.toContainText(fullKey);
});
