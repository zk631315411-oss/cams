import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  testMatch: "actual-workflow.spec.ts",
  timeout: 60_000,
  use: {
    baseURL: process.env.QA_WEB_URL || "http://localhost:5180",
    launchOptions: { executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe" },
  },
  reporter: "line",
});
