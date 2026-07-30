import { expect, test } from "@playwright/test";


async function login(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page.getByLabel("账号").fill("admin");
  await page.getByLabel("密码").fill("admin-local-only");
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page.getByRole("heading", { name: "题目工作台" })).toBeVisible();
}


test("desktop question and evidence workflow renders", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 960 });
  await login(page);
  await expect(page.locator("tbody tr")).toHaveCount(100);
  await page.screenshot({ path: "test-results/question-list-desktop.png", fullPage: true });
  await page.getByText("v7_q_000003", { exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.getByRole("button", { name: "打开证据面板" }).click();
  await expect(page.getByText("教材证据", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/question-detail-evidence.png", fullPage: true });
});


test("mobile list remains usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await expect(page.getByRole("button", { name: "打开导航" })).toBeVisible();
  await expect(page.locator("tbody tr").first()).toContainText("v7_q_");
  await page.screenshot({ path: "test-results/question-list-mobile.png" });
});
