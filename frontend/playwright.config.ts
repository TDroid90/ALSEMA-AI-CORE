import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./node_modules/.cache/playwright-results",
  timeout: 30_000,
  use: {
    baseURL: "http://localhost:5173",
    colorScheme: "dark",
  },
});
