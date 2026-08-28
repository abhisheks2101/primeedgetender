import { execSync } from "node:child_process";
import { expect, test } from "@playwright/test";

const backendUrl = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const adminEmail = process.env.E2E_ADMIN_EMAIL || "e2e.admin@example.com";
const adminPassword = process.env.E2E_ADMIN_PASSWORD || "Password123";

test.beforeAll(async () => {
  try {
    execSync(
      `cd ../backend && . .venv/bin/activate && python -m app.cli create-admin --email ${adminEmail} --full-name "E2E Admin" --password ${adminPassword}`,
      { stdio: "ignore" },
    );
  } catch {
    // Admin may already exist.
  }

  const loginResponse = await fetch(`${backendUrl}/api/auth/login`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email: adminEmail, password: adminPassword }),
  });
  expect(loginResponse.status).toBe(200);
});

async function login(page: import("@playwright/test").Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/app$/, { timeout: 10000 });
}

test.describe("Tender document administration", () => {
  test("admin opens tender document processing area", async ({ page }) => {
    await login(page, adminEmail, adminPassword);
    await page.getByRole("link", { name: "Tender Documents" }).click();
    await expect(page).toHaveURL(/\/admin\/tender-documents$/);
    await expect(page.getByRole("heading", { level: 1, name: "Tender Documents" })).toBeVisible();
    await expect(page.getByText("Module 8 prepares documents")).toBeVisible();
  });
});
