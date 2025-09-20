import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False so you can see login
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto("https://www.instagram.com/accounts/login/")

        print("➡️ Please log in manually in the browser window...")
        await page.wait_for_timeout(60000)  # give yourself 60 seconds to log in

        # Save cookies + storage state after login
        await context.storage_state(path="auth_state.json")
        print("✅ Login session saved to auth_state.json")

        await browser.close()

asyncio.run(main())
