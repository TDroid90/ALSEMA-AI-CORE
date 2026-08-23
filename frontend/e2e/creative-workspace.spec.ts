import { expect, test } from "@playwright/test";

const email = process.env.INITIAL_ADMIN_EMAIL;
const password = process.env.INITIAL_ADMIN_PASSWORD;
const accessToken = process.env.ALSEMA_E2E_TOKEN;

test("opens the native styled creative workspace in the ALSEMA session", async ({ page }) => {
  test.skip(
    !accessToken && (!email || !password),
    "ALSEMA administrator credentials or a short-lived E2E token are required",
  );
  if (accessToken) {
    await page.route("**/api/v1/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ access_token: accessToken, token_type: "bearer" }),
      });
    });
  }
  await page.goto("/creativo");
  await page.getByLabel("Correo").fill(email ?? "e2e@alsema.local");
  await page.getByLabel("Contraseña").fill(password ?? "short-lived-e2e-token");
  await page.getByRole("button", { name: "Ingresar" }).click();

  await expect(page).toHaveURL(/\/creativo$/);
  await expect(page.getByRole("heading", { name: "Creativo" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Secciones de Creativo" })).toBeVisible();
  await expect(page.locator(".creative-form-card").first()).toHaveCSS("background-color", "rgb(20, 20, 20)");
  await expect(page.locator(".creative-generate")).toHaveCSS(
    "background-color",
    "rgb(0, 194, 255)",
  );
});
