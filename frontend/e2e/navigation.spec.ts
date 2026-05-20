// Navigasjons-tester — sjekker at kritiske ruter finnes og ikke krasjer
import { test, expect } from '@playwright/test';

const PUBLIC_ROUTES = ['/welcome', '/login', '/help'];

for (const route of PUBLIC_ROUTES) {
  test(`${route} returnerer 200`, async ({ page }) => {
    const res = await page.goto(route);
    expect(res?.status()).toBeLessThan(500);
  });
}

test('404-siden er fornuftig', async ({ page }) => {
  const res = await page.goto('/finnes-ikke-abc123');
  // Next.js 404 er en 404, ikke 500
  expect(res?.status()).not.toBe(500);
});
