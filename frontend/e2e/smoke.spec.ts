// Smoke-tester — kjøres mot produksjon (ingen innlogging nødvendig for disse)
import { test, expect } from '@playwright/test';

test.describe('Smoke — offentlige sider', () => {
  test('velkomstsiden laster', async ({ page }) => {
    await page.goto('/welcome');
    await expect(page).toHaveTitle(/BEFS|Bufetat/i);
  });

  test('login-siden eksisterer', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[type="email"], input[placeholder*="E-post"], input[placeholder*="mail"]').first()).toBeVisible();
  });

  test('hjelp-siden er tilgjengelig', async ({ page }) => {
    await page.goto('/help');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });
});

test.describe('Smoke — redirect/auth-gate', () => {
  test('fdvu uten auth er ikke 500', async ({ page }) => {
    const response = await page.goto('/fdvu');
    expect(response?.status()).not.toBe(500);
  });

  test('onboarding er ikke 500', async ({ page }) => {
    const response = await page.goto('/onboarding');
    expect(response?.status()).not.toBe(500);
  });
});
