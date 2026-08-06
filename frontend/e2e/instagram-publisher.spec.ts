import { expect, test } from "@playwright/test";

test("shows secure Instagram configuration and a ready container without publishing", async ({ page }) => {
  let publishCalls = 0;
  await page.route("http://localhost:8000/api/v1/**", async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === "/api/v1/setup/status") return route.fulfill({ json: { setup_required: false } });
    if (path === "/api/v1/auth/login") return route.fulfill({ json: { access_token: "test-session" } });
    if (path === "/api/v1/providers/ollama/models") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/conversations") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/models/sync") return route.fulfill({ json: {} });
    if (path === "/api/v1/models") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/plugins/instagram/accounts") {
      return route.fulfill({ json: { items: [{ id: "11111111-1111-1111-1111-111111111111", account_label: "Cuenta editorial", app_id: "123", instagram_user_id: "17841400000000000", api_version: "v23.0", enabled: true, auto_publish: false, app_secret_configured: true, access_token_configured: true, last_connection_status: "connected" }] } });
    }
    if (path === "/api/v1/plugins/instagram/media") {
      return route.fulfill({ json: { items: [{ id: "22222222-2222-2222-2222-222222222222", account_id: "11111111-1111-1111-1111-111111111111", account_label: "Cuenta editorial", placement: "feed", caption: "Resumen periodístico de prueba", image_url: "https://images.example.com/test.jpg", status: "ready", container_id: "container-123", created_at: "2026-08-05T12:00:00Z" }] } });
    }
    if (path.endsWith("/publish")) {
      publishCalls += 1;
      return route.fulfill({ json: { status: "queued" } });
    }
    return route.fulfill({ status: 404, json: { detail: `Unhandled test route ${path}` } });
  });

  await page.goto("/");
  await page.getByLabel("Correo").fill("admin@example.test");
  await page.getByLabel("Contraseña").fill("test-password");
  await page.getByRole("button", { name: "Ingresar" }).click();
  await page.getByRole("button", { name: "Instagram" }).click();

  await expect(page.getByRole("heading", { name: "Instagram Publisher" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Probar conexión" })).toBeVisible();
  await expect(page.getByLabel("Access Token")).toHaveAttribute("type", "password");
  await expect(page.getByText("Resumen periodístico de prueba")).toBeVisible();
  await expect(page.getByRole("button", { name: "Confirmar y publicar" })).toBeVisible();
  expect(publishCalls).toBe(0);
});
