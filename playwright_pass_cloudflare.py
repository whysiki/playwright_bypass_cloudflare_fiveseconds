import re
import cv2
import numpy as np
from playwright.sync_api import Playwright, sync_playwright, Page, Browser
from playwright.async_api import async_playwright
import playwright.async_api
from PIL import Image
import random
import time
from pathlib import Path
from bs4 import BeautifulSoup
from rich import print
import pyautogui
import asyncio

current_file_path = Path(__file__).resolve().parent
cache_path = current_file_path / "cache"
cache_path.mkdir(exist_ok=True)
template_path = current_file_path / "square.png"
div_screenshot_path = cache_path / "div_screenshot.png"
div_screenshot_no_white_path = cache_path / "div_screenshot_no_white.png"
screen_path = cache_path / "screen.png"
state_path = cache_path / "state.json"


def pure_html_remove_css_and_js(html: str) -> str:
    return re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.DOTALL)


def is_page_unblocked(text: str) -> bool:
    blocked_conditions = (
        "cloudflare" in text.lower(),
        "just a moment" in text.lower(),
        "enable javascript" in text.lower(),
        "verifying you are human" in text.lower(),
    )
    return not any(blocked_conditions)


def remove_right_white_background(image_path: str, output_path: str) -> None:
    image = Image.open(image_path).convert("RGBA")
    data = np.array(image)

    non_white_mask = np.all(data[:, :, :3] <= 210, axis=-1)

    if np.any(non_white_mask):
        right_bound = np.max(np.where(non_white_mask)[1]) + 1
    else:
        right_bound = data.shape[1]
    cropped_image = Image.fromarray(data[:, :right_bound])
    cropped_image.save(output_path)


def bypass_cloudflare(browser: Browser, url: str) -> None:
    context = browser.new_context()
    page = context.new_page()
    page.goto(url)
    while True:
        try:
            page.wait_for_load_state("domcontentloaded")
            html = page.content()
            if is_page_unblocked(html):
                soup = BeautifulSoup(pure_html_remove_css_and_js(html), "html.parser")
                htm_plaintext = soup.select_one("html").text
                print(htm_plaintext)
                print("[green]Page is unblocked[/green]")
                context.storage_state(path=state_path)
                break
            else:
                print("[red]Blocked by cloudflare[/red]")
                print(f"current url: {page.url}")
            div_element = page.query_selector("#kGtPC2 > div > div")
            if div_element:
                print("security check div_element found")
                bounding_box = div_element.bounding_box()
                if bounding_box:
                    width = bounding_box["width"]
                    height = bounding_box["height"]
                    if width > 0 and height > 0:
                        print("security check div_element width and height > 0, loaded")
                        div_element.screenshot(path=div_screenshot_path)
                        print(f"div_screenshot_path: {div_screenshot_path}")
                        page.wait_for_timeout(random.randint(500, 1000))
                        square_template_ndarray = cv2.imread(
                            template_path, cv2.IMREAD_GRAYSCALE
                        )
                        remove_right_white_background(
                            div_screenshot_path, div_screenshot_no_white_path
                        )
                        print(
                            f"div_screenshot_no_white_path: {div_screenshot_no_white_path}"
                        )
                        div_screenshot_no_white_ndarray = cv2.imread(
                            div_screenshot_no_white_path, cv2.IMREAD_GRAYSCALE
                        )
                        result = cv2.matchTemplate(
                            div_screenshot_no_white_ndarray,
                            square_template_ndarray,
                            cv2.TM_CCOEFF_NORMED,
                        )
                        threshold = 0.5
                        loc_div = np.where(result >= threshold)
                        if len(loc_div[0]) > 2:
                            print("checkbox found in security check div_element")
                            average_loc_squareIn_div = np.mean(loc_div, axis=1)
                            pyautogui.screenshot(screen_path)
                            print(f"full screen screenshot path: {screen_path}")
                            full_screen_shot = cv2.imread(
                                screen_path, cv2.IMREAD_GRAYSCALE
                            )
                            result = cv2.matchTemplate(
                                full_screen_shot,
                                div_screenshot_no_white_ndarray,
                                cv2.TM_CCOEFF_NORMED,
                            )
                            threshold = 0.6
                            loc_screen = np.where(result >= threshold)
                            if len(loc_screen[0]) > 2:
                                print("security check div_element found in screen")
                                average_loc_divIn_screen = np.mean(loc_screen, axis=1)
                                screen_x = average_loc_divIn_screen[
                                    0
                                ]  # div在屏幕截图中的位置
                                screen_y = average_loc_divIn_screen[1]
                                result_x = (
                                    screen_x
                                    + average_loc_squareIn_div[0]
                                    + square_template_ndarray.shape[0] // 6
                                )  # square在屏幕截图中的位置
                                result_y = (
                                    screen_y
                                    + average_loc_squareIn_div[1]
                                    + square_template_ndarray.shape[1] // 3
                                )
                                result_x, result_y = (
                                    result_y,
                                    result_x,
                                )  # x, y坐标颠倒
                                print(
                                    f"caculated result_x: {result_x}, result_y: {result_y}"
                                )
                                pyautogui.click(
                                    x=result_x,
                                    y=result_y,
                                    duration=random.uniform(0.1, 0.3),
                                )
                                print("click success")

            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            page.reload()
            page.wait_for_load_state("domcontentloaded")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        with playwright.firefox.launch(headless=False) as browser:
            bypass_cloudflare(browser, "https://cn.investing.com/")

    # async def main():
    #     async with async_playwright() as playwright:
    #         browser = await playwright.firefox.launch(headless=False)
    #         await bypass_cloudflare_async(
    #             browser, "https://cn.investing.com/", max_time=60
    #         )

    # asyncio.run(main())
