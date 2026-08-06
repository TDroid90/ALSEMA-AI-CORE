import { expect, test } from "@playwright/test";

test("shows Facebook feed and story publishing with Spanish text", async ({ page }) => {
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
    if (path === "/api/v1/plugins/facebook/accounts") {
      return route.fulfill({ json: { items: [{ id: "11111111-1111-1111-1111-111111111111", account_label: "Página editorial", app_id: "123", page_id: "123450000000000", api_version: "v26.0", enabled: true, auto_publish: false, app_secret_configured: true, page_access_token_configured: true, last_connection_status: "connected" }] } });
    }
    if (path === "/api/v1/plugins/facebook/media") {
      return route.fulfill({ json: { items: [{ id: "22222222-2222-2222-2222-222222222222", account_id: "11111111-1111-1111-1111-111111111111", account_label: "Página editorial", placement: "story", caption: "Última información: educación, economía y acción 🇦🇷", image_url: "https://images.example.com/story.jpg", status: "ready", photo_id: "photo-123", created_at: "2026-08-06T12:00:00Z" }] } });
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
  await page.getByRole("button", { name: "Facebook" }).click();

  await expect(page.getByRole("heading", { name: "Facebook Publisher" })).toBeVisible();
  await expect(page.getByLabel("Page Access Token")).toHaveAttribute("type", "password");
  await expect(page.getByText("Última información: educación, economía y acción 🇦🇷")).toBeVisible();
  await expect(page.getByText("Historia", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Confirmar y publicar" })).toBeVisible();
  expect(publishCalls).toBe(0);
});
