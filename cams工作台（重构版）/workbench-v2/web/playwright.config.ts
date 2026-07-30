import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  testIgnore: "**/actual-workflow.spec.ts",
  timeout: 30_000,
  use: {
    baseURL: "http://localhost:5174",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    },
  },
  reporter: "line",
});
