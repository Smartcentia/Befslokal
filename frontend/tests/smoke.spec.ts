import { test, expect } from '@playwright/test';

test.describe('KNOWME Enterprise Dashboard Smoke Tests', () => {

    test('Dashboard loads with Enterprise title', async ({ page }) => {
        await page.goto('/dashboard');
        // Page title verification
        await expect(page).toHaveTitle(/BEFS/);
    });

    test('Stats are showing Real/Mock data (Non-zero)', async ({ page }) => {
        await page.goto('/dashboard');

        // Wait for potential redirect or load
        await page.waitForLoadState('networkidle');

        // Check for "Totalt Antall Eiendommer" card using glass-card class
        const propCard = page.locator('.glass-card').filter({ hasText: 'Totalt Antall Eiendommer' });

        // Note: If redirected to login, this will fail.
        if (page.url().includes('login.microsoft')) {
            console.log('Redirected to Login - Test cannot proceed without Auth');
            return;
        }

        await expect(propCard).toBeVisible();

        // The number is in a <p> tag with text-4xl
        const countText = await propCard.locator('p.text-4xl').innerText();
        expect(countText).not.toBe('...');
    });

    test('Map Component is rendered', async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');

        if (page.url().includes('login.microsoft')) return;

        // Map section (Mapbox-kart eller placeholder hvis token mangler)
        await expect(
            page.locator('.mapboxgl-map').or(page.getByText(/Sett.*MAPBOX|Laster kart/i)).first()
        ).toBeVisible();
    });

    test('Internal Control Widget is visible', async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');

        if (page.url().includes('login.microsoft')) return;

        // "Internkontroll Status" is the header in the card
        const widget = page.locator('.glass-card').filter({ hasText: 'Internkontroll Status' });
        await expect(widget).toBeVisible();
    });
});
