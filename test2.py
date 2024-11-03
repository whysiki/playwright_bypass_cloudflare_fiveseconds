from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from playwright_pass_cloudflare import *


def run(playwright):
    browser = playwright.firefox.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Apply stealth plugin
    stealth_sync(page)

    page.goto("https://cn.investing.com/")

    while True:
        try:
            page.wait_for_load_state("domcontentloaded")
            html = page.content()
            if is_page_unblocked(html):
                print("[green]Page is unblocked[/green]")
                break
            else:
                print("[red]Blocked by cloudflare[/red]")
                print(f"current url: {page.url}")
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            page.reload()
            page.wait_for_load_state("domcontentloaded")

    browser.close()


with sync_playwright() as playwright:
    run(playwright)
