import { expect, test } from '@playwright/test';

test('desktop web shell smoke renders and can capture progress screenshot', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Gitplant Desktop' })).toBeVisible();
  await expect(page.getByText('No recent documents.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Dev scaffolding' })).toBeVisible();
  await page.screenshot({ path: 'artifacts/screenshots/desktop-smoke.png', fullPage: true });
});
