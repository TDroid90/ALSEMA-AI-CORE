import { expect, test } from "@playwright/test";

test("loads the ALSEMA design system instead of browser-default controls", async ({ page }) => {
  await page.goto("/");

  await expect(page.locator("body")).toHaveCSS("background-color", "rgb(11, 11, 11)");
  await expect(page.locator("aside")).toHaveCSS("background-color", "rgb(20, 20, 20)");

  const input = page.locator("input").first();
  await expect(input).toHaveCSS("background-color", "rgb(11, 11, 11)");
  await expect(input).toHaveCSS("color", "rgb(242, 242, 242)");

  const button = page.locator("button").first();
  await expect(button).toHaveCSS("border-top-color", "rgb(0, 194, 255)");
  await expect(button).toHaveCSS("min-height", "40px");
});
