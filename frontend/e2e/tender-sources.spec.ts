import { execSync } from "node:child_process";
import { expect, test } from "@playwright/test";

const backendUrl = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const adminEmail = process.env.E2E_ADMIN_EMAIL || "e2e.admin@example.com";
const adminPassword = process.env.E2E_ADMIN_PASSWORD || "Password123";
const userEmail = process.env.E2E_TEST_EMAIL || "e2e.user@example.com";
const userPassword = process.env.E2E_TEST_PASSWORD || "Password123";
const userFullName = process.env.E2E_TEST_FULL_NAME || "E2E Test User";

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

async function ensureUserAccount() {
  const registerResponse = await fetch(`${backendUrl}/api/auth/register`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: userEmail,
      password: userPassword,
      full_name: userFullName,
    }),
  });

  if (registerResponse.status === 201) {
    return;
  }

  if ([400, 403, 409].includes(registerResponse.status)) {
    const loginCheck = await fetch(`${backendUrl}/api/auth/login`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email: userEmail, password: userPassword }),
    });
    expect(loginCheck.status).toBe(200);
    return;
  }

  throw new Error(`Unexpected registration status: ${registerResponse.status}`);
}

async function login(page: import("@playwright/test").Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/app$/, { timeout: 10000 });
}

test.describe("Tender source administration", () => {
  test("admin manages fictional tender sources", async ({ page }) => {
    await login(page, adminEmail, adminPassword);
    await page.getByRole("link", { name: "Tender Sources" }).click();
    await expect(page).toHaveURL(/\/admin\/tender-sources$/);
    await expect(page.getByRole("heading", { level: 1, name: "Tender Sources" })).toBeVisible();

    const suffix = Date.now().toString();
    await page.getByRole("link", { name: "Create Source" }).click();
    await page.getByLabel("Source Name").fill(`Fictional Source ${suffix}`);
    await page.getByLabel("Source Code").fill(`TEST_${suffix}`);
    await page.getByLabel("State").fill("Demo State");
    await page.getByLabel("Authority").fill("Demo Authority");
    await page.getByLabel("Portal URL").fill("https://example.test/portal");
    await page.getByLabel("Configuration Source URL").fill("https://example.test/source");
    await page.getByRole("button", { name: "Create Source" }).click();
    await expect(page.getByRole("heading", { level: 1, name: `Fictional Source ${suffix}` })).toBeVisible();

    await page.getByRole("link", { name: "Back to Sources" }).click();
    await expect(page.getByRole("link", { name: `Fictional Source ${suffix}` })).toBeVisible();

    await page.getByRole("link", { name: `Fictional Source ${suffix}` }).click();
    await expect(page.getByText("Collection History")).toBeVisible();
    await page.getByRole("button", { name: "Disable Source" }).click();
    await expect(page.getByText("Inactive")).toBeVisible();
  });

  test("regular user cannot create tender sources", async ({ page }) => {
    await ensureUserAccount();
    await login(page, userEmail, userPassword);
    await page.goto("/admin/tender-sources/new");
    await expect(page).toHaveURL(/\/admin\/tender-sources$/);
  });
});
