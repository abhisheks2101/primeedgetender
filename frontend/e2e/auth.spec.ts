import { expect, test } from "@playwright/test";

const email = process.env.E2E_TEST_EMAIL || "e2e.user@example.com";
const password = process.env.E2E_TEST_PASSWORD || "Password123";
const fullName = process.env.E2E_TEST_FULL_NAME || "E2E Test User";

test.beforeAll(async () => {
  const backendUrl = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const registerResponse = await fetch(`${backendUrl}/api/auth/register`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      password,
      full_name: fullName,
    }),
  });

  if (registerResponse.status === 201) {
    return;
  }

  if ([400, 403].includes(registerResponse.status)) {
    const loginCheck = await fetch(`${backendUrl}/api/auth/login`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });
    expect(loginCheck.status).toBe(200);
    return;
  }

  throw new Error(`Unexpected registration status: ${registerResponse.status}`);
});

test.describe("Authentication", () => {
  test("valid login flow", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page).toHaveURL(/\/app$/);
    await expect(page.getByText("Authentication successfully configured.")).toBeVisible();
    await expect(page.getByText(fullName)).toBeVisible();
  });

  test("invalid login shows error", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill("WrongPassword123");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByText("Invalid email or password.")).toBeVisible();
    await expect(page).toHaveURL(/\/login$/);
  });

  test("protected page redirects when unauthenticated", async ({ page, context }) => {
    await context.clearCookies();
    await page.goto("/app");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("authenticated page persists after refresh", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/app$/);

    await page.reload();
    await expect(page.getByText(fullName)).toBeVisible();
    await expect(page.getByText("Authentication successfully configured.")).toBeVisible();
  });

  test("logout clears session and protects /app", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/app$/);

    await page.getByRole("button", { name: "Logout" }).click();
    await expect(page).toHaveURL(/\/login$/);

    await page.goto("/app");
    await expect(page).toHaveURL(/\/login$/);
  });
});
