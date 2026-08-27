import { execSync } from "node:child_process";
import { expect, test } from "@playwright/test";
import path from "node:path";

const adminEmail = process.env.E2E_ADMIN_EMAIL || "e2e.admin@example.com";
const adminPassword = process.env.E2E_ADMIN_PASSWORD || "Password123";

test.beforeAll(async () => {
  const backendUrl = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  try {
    execSync(
      `cd ../backend && . .venv/bin/activate && python -m app.cli create-admin --email ${adminEmail} --full-name "E2E Admin" --password ${adminPassword}`,
      { stdio: "ignore" },
    );
  } catch {
    // Admin may already exist from a previous run.
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

async function login(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(adminEmail);
  await page.getByLabel("Password").fill(adminPassword);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/app$/);
}

test.describe("Company management", () => {
  test("create two companies and verify isolation", async ({ page }) => {
    await login(page);
    await page.getByRole("link", { name: "Open Companies" }).click();
    await expect(page).toHaveURL(/\/app\/companies$/);

    const suffix = Date.now().toString();

    await page.getByRole("link", { name: "Create Company" }).click();
    await page.getByLabel("Legal Name").fill(`Fictional Company A Legal ${suffix}`);
    await page.getByLabel("Display Name").fill(`Fictional Company A ${suffix}`);
    await page.getByLabel("Entity Type").fill("Private Limited");
    await page.getByLabel("State").fill("Demo State A");
    await page.getByRole("button", { name: "Create Company" }).click();
    await expect(page.getByRole("heading", { level: 1, name: `Fictional Company A ${suffix}` })).toBeVisible();

    await page.getByRole("link", { name: "Companies" }).click();
    await page.getByRole("link", { name: "Create Company" }).click();
    await page.getByLabel("Legal Name").fill(`Fictional Company B Legal ${suffix}`);
    await page.getByLabel("Display Name").fill(`Fictional Company B ${suffix}`);
    await page.getByLabel("Entity Type").fill("Partnership");
    await page.getByLabel("State").fill("Demo State B");
    await page.getByRole("button", { name: "Create Company" }).click();
    await expect(page.getByRole("heading", { level: 1, name: `Fictional Company B ${suffix}` })).toBeVisible();

    await page.getByRole("link", { name: "Companies" }).click();
    await expect(page.getByText(`Fictional Company A ${suffix}`)).toBeVisible();
    await expect(page.getByText(`Fictional Company B ${suffix}`)).toBeVisible();

    await page.getByRole("link", { name: `Fictional Company A ${suffix}` }).click();
    await page.getByRole("button", { name: "Experience" }).click();
    await page.getByPlaceholder("Project name").fill("Fictional Road Project");
    await page.getByPlaceholder("Work category").fill("ROAD_CONSTRUCTION");
    await page.getByRole("button", { name: "Add Project" }).click();
    await expect(page.getByText("Fictional Road Project")).toBeVisible();

    await page.getByRole("button", { name: "Documents" }).click();
    const testFile = path.join(process.cwd(), "e2e", "fixtures", "sample.pdf");
    await page.locator("#document-type").focus();
    await page.locator("#document-file").setInputFiles(testFile);
    await page.getByRole("button", { name: "Upload Document" }).click();
    await expect(page.getByText("Document uploaded.")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("sample.pdf")).toBeVisible();

    await page.getByRole("link", { name: "Companies" }).click();
    await page.getByRole("link", { name: `Fictional Company B ${suffix}` }).click();
    await page.getByRole("button", { name: "Experience" }).click();
    await expect(page.getByText("Fictional Road Project")).not.toBeVisible();
    await page.getByRole("button", { name: "Documents" }).click();
    await expect(page.getByText("sample.pdf")).not.toBeVisible();
  });
});
