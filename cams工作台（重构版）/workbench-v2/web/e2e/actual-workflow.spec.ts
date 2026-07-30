import { expect, test } from "@playwright/test";

const API = process.env.QA_API_URL || "http://127.0.0.1:8020";
const password = "qa-workflow-password";
const runId = Date.now().toString();
const editorName = `qa-editor-${runId}`;
const secondEditorName = `qa-editor-two-${runId}`;
const reviewerName = `qa-reviewer-${runId}`;
const releaseTitle = `QA 实际使用交付批次 ${runId}`;
const questionId = "v7_q_000003";

async function loginApi(request: import("@playwright/test").APIRequestContext, username: string, value: string) {
  const response = await request.post(`${API}/api/auth/login`, { data: { username, password: value } });
  expect(response.ok()).toBeTruthy();
  return { Authorization: `Bearer ${(await response.json()).access_token}` };
}

async function loginPage(page: import("@playwright/test").Page, username: string, value = password) {
  await page.goto("/");
  await page.getByLabel("账号").fill(username);
  await page.getByLabel("密码").fill(value);
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page.getByRole("heading", { name: "题目工作台" })).toBeVisible();
}

test("human editing, review, release, and publication workflow", async ({ page, request }) => {
  const admin = await loginApi(request, "admin", "admin-local-only");
  for (const [username, role] of [[editorName, "editor"], [secondEditorName, "editor"], [reviewerName, "reviewer"]]) {
    const response = await request.post(`${API}/api/users`, { headers: admin, data: { username, password, role } });
    expect(response.ok()).toBeTruthy();
  }
  const editor = await loginApi(request, editorName, password);

  await page.setViewportSize({ width: 1440, height: 960 });
  await loginPage(page, editorName);
  await expect(page.getByRole("heading", { name: "题目工作台" })).toBeVisible();
  await page.getByLabel("小节编号").fill("p3-ch8-h3");
  await page.getByLabel("小节内题号").fill("1");
  await page.getByLabel("小节内题号").press("Enter");
  await expect(page.getByText(questionId, { exact: true })).toBeVisible();
  await page.getByText(questionId, { exact: true }).click();

  const before = await (await request.get(`${API}/api/questions/${questionId}`, { headers: editor })).json();
  const oldAnswerIds = before.current_version.answer_option_ids;
  page.once("dialog", (dialog) => dialog.accept("实际使用验收：英文题干与选项调整"));
  await page.getByRole("button", { name: "开始编辑" }).click();
  await expect(page.getByText("本题已锁定")).toBeVisible();

  const secondEditor = await loginApi(request, secondEditorName, password);
  const lockAttempt = await request.post(`${API}/api/questions/${questionId}/tasks`, {
    headers: secondEditor,
    data: { purpose: "must be rejected" },
  });
  expect(lockAttempt.status()).toBe(409);

  const englishStem = page.getByLabel("English stem");
  await englishStem.fill(`${await englishStem.inputValue()} QA`);
  await page.getByRole("button", { name: "下移选项" }).first().click();
  await page.getByRole("button", { name: "打开证据面板" }).click();
  const evidenceSearch = page.getByPlaceholder("unit、术语或原文");
  await evidenceSearch.fill("board");
  await evidenceSearch.press("Enter");
  const availableCorePoint = page.locator("button:not([disabled])").filter({ hasText: "设为主 CP" }).first();
  await expect(availableCorePoint).toBeVisible();
  await availableCorePoint.click();
  await page.getByRole("button", { name: "保存版本" }).click();
  await expect(page.getByText("已创建不可变版本")).toBeVisible();

  const changed = await (await request.get(`${API}/api/questions/${questionId}`, { headers: editor })).json();
  expect(changed.current_version.answer_option_ids).toEqual(oldAnswerIds);
  expect(changed.current_version.bindings.primary_cp_id).toBeTruthy();
  const taskId = changed.current_version.task_id;
  const diff = await request.get(`${API}/api/tasks/${taskId}/diff`, { headers: editor });
  expect(diff.ok()).toBeTruthy();
  expect((await diff.json()).diff).toContain("QA");

  await page.getByRole("button", { name: "结束任务" }).click();
  await expect(page.getByText("编辑任务已结束，尚未提交审核")).toBeVisible();
  await page.getByRole("button", { name: "提交审核" }).click();
  await expect(page.getByText("已提交审核")).toBeVisible();

  await page.getByRole("button", { name: "退出登录" }).click();
  await loginPage(page, reviewerName);
  await page.goto("/#/reviews");
  const pendingReview = page.locator(".review-row").filter({ has: page.getByRole("button", { name: "领取" }) }).first();
  await expect(pendingReview).toContainText(questionId);
  await pendingReview.getByRole("button", { name: "领取" }).click();
  page.once("dialog", (dialog) => dialog.accept("审核通过：版本、答案与证据均已核对"));
  const inReview = page.locator(".review-row").filter({ has: page.getByRole("button", { name: "批准" }) }).first();
  await expect(inReview).toContainText(questionId);
  await inReview.getByRole("button", { name: "批准" }).click();
  await expect(page.getByText("已批准", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "退出登录" }).click();
  await loginPage(page, "admin", "admin-local-only");
  await page.goto("/#/releases");
  await expect(page.getByRole("heading", { name: "发布批次" })).toBeVisible();
  await expect(page.getByText(questionId, { exact: true })).toBeVisible();
  await page.getByPlaceholder("批次名称").fill(releaseTitle);
  await page.locator(".approved-picker input[type=checkbox]").check();
  await page.getByRole("button", { name: "创建批次" }).click();
  await expect(page.getByText(releaseTitle, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "生成 DOCX" }).click();
  await expect(page.getByText("下载 DOCX", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "标记已录入" }).click();
  await page.getByRole("button", { name: "标记已核对" }).click();
  await page.getByRole("button", { name: "标记已发布" }).click();
  await expect(page.getByText("已发布", { exact: true })).toBeVisible();

  const finalQuestion = await (await request.get(`${API}/api/questions/${questionId}`, { headers: admin })).json();
  expect(finalQuestion.status).toBe("published");
  expect(finalQuestion.published_version_id).toBe(finalQuestion.current_version_id);
  const releases = await (await request.get(`${API}/api/releases`, { headers: admin })).json();
  const release = releases.find((item: { title: string }) => item.title === releaseTitle);
  const downloaded = await request.get(`${API}/api/releases/${release.id}/download`, { headers: admin });
  expect(downloaded.status()).toBe(200);
  expect(downloaded.headers()["content-type"]).toContain("wordprocessingml.document");
  await page.screenshot({ path: "test-results/actual-workflow-published.png", fullPage: true });
});
