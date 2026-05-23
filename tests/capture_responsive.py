import asyncio
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        sizes = [
            {"width": 1440, "height": 900, "name": "1440px"},
            {"width": 1024, "height": 768, "name": "1024px"},
            {"width": 768, "height": 1024, "name": "768px"},
            {"width": 425, "height": 800, "name": "425px"}
        ]
        
        for size in sizes:
            context = await browser.new_context(viewport={"width": size["width"], "height": size["height"]})
            page = await context.new_page()
            await page.goto("http://127.0.0.1:5000/student?demo=1")
            
            # Wait for any animations to finish
            await page.wait_for_timeout(3000)
            
            filename = f"capture_{size['name']}.png"
            await page.screenshot(path=filename, full_page=True)
            print(f"Captured {filename}")
            await context.close()
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture())
