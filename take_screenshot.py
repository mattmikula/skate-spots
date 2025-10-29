#!/usr/bin/env python3
"""Simple screenshot tool using selenium-wire or requests + html2image"""
import asyncio
import sys
try:
    from playwright.async_api import async_playwright

    async def take_screenshot():
        async with async_playwright() as p:
            # Try to use existing system chrome if available
            browser = None
            try:
                browser = await p.chromium.launch(
                    channel="chrome",
                    headless=True
                )
            except:
                try:
                    browser = await p.chromium.launch(headless=True)
                except:
                    print("Error: Could not launch browser")
                    return False

            if browser:
                page = await browser.new_page(viewport={"width": 1920, "height": 1080})
                await page.goto("http://localhost:8000")
                await page.wait_for_load_state("networkidle")
                await page.screenshot(path="homepage_screenshot.png", full_page=True)
                await browser.close()
                print("Screenshot saved to homepage_screenshot.png")
                return True
            return False

    asyncio.run(take_screenshot())
except ImportError:
    print("Playwright not available, using alternative method")
    # Alternative: Just fetch the HTML and describe it
    import urllib.request
    with urllib.request.urlopen('http://localhost:8000') as response:
        html = response.read().decode('utf-8')
        print("Successfully fetched homepage HTML")
        print(f"HTML length: {len(html)} characters")
