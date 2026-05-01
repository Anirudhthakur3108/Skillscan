import { test, expect } from '@playwright/test';

test.describe('SkillScan Full Flow', () => {
  // We'll use a random email for each test run
  const testId = Date.now();
  const testEmail = `student${testId}@example.com`;
  const testPassword = 'password123';

  test('should complete full assessment and learning plan journey', async ({ page }) => {
    test.setTimeout(180000); // Allow 3 minutes for full flow with AI processing
    // 1. Register a new user
    await page.goto('/register');
    await page.fill('input[type="text"]', `Student ${testId}`);
    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', testPassword);
    await page.click('button[type="submit"]');

    // Wait for navigation to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('text=Welcome back')).toBeVisible();

    // 2. Add a skill
    await page.click('button:has-text("Add / Verify Skills")');
    await expect(page).toHaveURL('/skills');
    
    // Switch to Manual Entry tab
    await page.locator('button').filter({ hasText: 'Manual Entry' }).click();
    await page.waitForSelector('input[placeholder="Skill Name (e.g. React, Python)"]', { state: 'visible' });

    // Enter skill name and press Enter to add
    await page.fill('input[placeholder="Skill Name (e.g. React, Python)"]', 'Docker');
    await page.keyboard.press('Enter');

    // Click Confirm Skills
    await page.click('button:has-text("Confirm Skills")');

    // Configure the skill (Difficulty and Proficiency)
    await page.waitForSelector('text=Configure Every Skill Before Initialization');
    
    // Select Difficulty (say, 5/10)
    await page.locator('label:has-text("Difficulty") >> select').selectOption('5');
    // Select Proficiency (say, 5/10)
    await page.locator('label:has-text("Claimed Proficiency") >> select').selectOption('5');

    // Save configuration
    await page.click('button:has-text("Save Skill Configuration")');

    // Initialize Dashboard
    await page.click('button:has-text("Initialize Dashboard")');

    // Wait for the skill card to appear on dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('div:has-text("Docker")').first()).toBeVisible();

    // 3. Take Assessment
    // Click 'Start Assessment' or 'Assess Now'
    await page.click('button:has-text("Assess Now")');

    // The assessment page should load. We'll wait for the first question.
    await expect(page.locator('text=Question 1 of')).toBeVisible({ timeout: 60000 });

    // Assuming we have up to 10 questions. We will loop and answer them.
    for (let i = 0; i < 10; i++) {
      // Wait for question to render
      await page.waitForTimeout(500);

      // Answer MCQ by clicking the first option button
      const optionButton = page.locator('button.w-full.p-6.rounded-2xl.border-2').first();
      const textArea = page.locator('textarea').first();

      if (await optionButton.isVisible()) {
        // Answer MCQ
        await optionButton.click();
      } else if (await textArea.isVisible()) {
        // Answer Coding/Case Study
        await textArea.fill('This is a mock answer for the playwright test.');
      }

      // Next or Submit
      const nextButton = await page.locator('button:has-text("Next")');
      const submitButton = await page.locator('button:has-text("Submit Assessment")');

      if (await nextButton.isVisible()) {
        await nextButton.click();
      } else if (await submitButton.isVisible()) {
        await submitButton.click();
      }
    }

    // 4. View Results
    // We should be redirected to the assessment result page
    await expect(page.getByText('Overall Score', { exact: true })).toBeVisible({ timeout: 90000 });

    // 5. Generate / View Learning Plan
    // First, let's wait a moment to see if we're already on the learning-plan page or if we have the Generate button
    if (page.url().includes('/learning-plan')) {
      // already there
    } else {
      const generatePlanButton = page.locator('button', { hasText: 'Generate Your Learning Plan' });
      if (await generatePlanButton.isVisible()) {
        await generatePlanButton.click();
        
        // After clicking, the button changes to 'Generating Personalized Plan...'
        // and then the page automatically navigates to /learning-plan?plan_id=xyz
        await expect(page).toHaveURL(/\/learning-plan/, { timeout: 90000 });
      } else {
        await page.goto('/learning-plan');
      }
    }

    // Wait for the Learning plan to load
    await expect(page.locator('h1:has-text("Your Learning Path")')).toBeVisible({ timeout: 60000 });
    // Verify the list contains Docker
    await expect(page.locator('button', { hasText: 'Docker' }).first()).toBeVisible({ timeout: 30000 });
    
    // Click it to view details (if it doesn't auto load)
    await page.locator('button:has-text("Docker")').first().click();

    // The title 'Learning Plan' or 'Docker' should show up in the plan details
    await expect(page.locator('h2:has-text("Learning Plan")').or(page.locator('h2:has-text("Docker")'))).toBeVisible({ timeout: 30000 });
    
    // Validate we have Phase or Timeline elements
    await expect(page.locator('text=Weeks').first()).toBeVisible({ timeout: 30000 });
  });
});
