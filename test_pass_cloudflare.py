import re
import cv2
import numpy as np
from playwright.sync_api import Playwright, sync_playwright, Page
import random
import time
from pathlib import Path
from bs4 import BeautifulSoup
from rich import print

current_file_path = Path(__file__).resolve().parent
template_path = current_file_path / "square.png"


def pure_html_remove_css_and_js(html: str) -> str:
    return re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.DOTALL)


def is_page_unblocked(text: str) -> bool:
    blocked_conditions = (
        "cloudflare" in text.lower(),
        "just a moment" in text.lower(),
        "checking your browser" in text.lower(),
        "enable javascript" in text.lower(),
        "verifying you are human" in text.lower(),
    )
    return not any(blocked_conditions)


def simulate_human_mouse_movement(
    page: Page,
    start_x: int | float,
    start_y: int | float,
    end_x: int | float,
    end_y: int | float,
):
    def bezier_curve(t, p0, p1, p2, p3):
        x = (
            (1 - t) ** 3 * p0[0]
            + 3 * (1 - t) ** 2 * t * p1[0]
            + 3 * (1 - t) * t**2 * p2[0]
            + t**3 * p3[0]
        )
        y = (
            (1 - t) ** 3 * p0[1]
            + 3 * (1 - t) ** 2 * t * p1[1]
            + 3 * (1 - t) * t**2 * p2[1]
            + t**3 * p3[1]
        )
        return x, y

    control_points = [
        (float(start_x), float(start_y)),
        (
            float(start_x) + random.uniform(-100, 100),
            float(start_y) + random.uniform(-100, 100),
        ),
        (
            float(end_x) + random.uniform(-100, 100),
            float(end_y) + random.uniform(-100, 100),
        ),
        (float(end_x), float(end_y)),
    ]

    steps = random.randint(50, 100)
    for i in range(steps):
        t = i / steps
        x, y = bezier_curve(t, *control_points)
        page.mouse.move(x, y)
        page.evaluate(
            f"""
            const dot = document.createElement('div');
            dot.className = 'showdot';
            dot.style.position = 'absolute';
            dot.style.width = '5px';
            dot.style.height = '5px';
            dot.style.backgroundColor = 'blue';
            dot.style.borderRadius = '50%';
            dot.style.left = '{x}px';
            dot.style.top = '{y}px';
            document.body.appendChild(dot);
            """
        )
        time.sleep(random.uniform(0.01, 0.05))
    page.mouse.click(end_x, end_y, delay=random.randint(100, 500))


def run1(playwright: Playwright) -> None:
    with playwright.firefox.launch(
        headless=False,
        # args=["--incognito", "--disable-gpu"],
    ) as browser:
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://cn.investing.com/")
        while True:
            time.sleep(1)
            html = page.content()
            if is_page_unblocked(html):
                soup = BeautifulSoup(pure_html_remove_css_and_js(html), "html.parser")
                htm_plaintext = soup.select_one("html").text
                print(htm_plaintext)
                print("[green]Page is unblocked[/green]")
                break
            else:
                print("[red]Blocked by cloudflare[/red]")
                print(f"current url: {page.url}")
            div_element = page.locator("#kGtPC2 > div > div")
            if div_element:
                print("div_element found")
                bounding_box = div_element.bounding_box()
                if bounding_box:
                    print(bounding_box)
                    x_start = bounding_box["x"]
                    y_start = bounding_box["y"]
                    width = bounding_box["width"]
                    height = bounding_box["height"]
                    if width > 0 and height > 0:
                        div_element.screenshot(path="div_screenshot.png")
                        page.wait_for_timeout(1000)  # 等待1秒
                        # 使用OpenCV在截图中匹配矩形点选框的位置
                        template = cv2.imread(
                            "square.png", cv2.IMREAD_GRAYSCALE
                        )  # 矩形点选框
                        screenshot = cv2.imread(
                            "div_screenshot.png", cv2.IMREAD_GRAYSCALE
                        )  # 截图
                        result = cv2.matchTemplate(
                            screenshot, template, cv2.TM_CCOEFF_NORMED
                        )
                        threshold = 0.5
                        loc = np.where(result >= threshold)
                        if len(loc[0]) > 2:
                            average_loc = np.mean(loc, axis=1)
                            click_x = x_start + average_loc[0]
                            click_y = y_start + average_loc[1] + template.shape[1] // 3
                            try:
                                click_x, click_y = float(click_x), float(click_y)
                                simulate_human_mouse_movement(
                                    page, 0, 0, click_x, click_y
                                )
                                page.evaluate(
                                    f"""
                                    const dot = document.createElement('div');
                                    dot.className = 'showdot';
                                    dot.style.position = 'absolute';
                                    dot.style.width = '10px';
                                    dot.style.height = '10px';
                                    dot.style.backgroundColor = 'red';
                                    dot.style.borderRadius = '50%';
                                    dot.style.left = '{click_x}px';
                                    dot.style.top = '{click_y}px';
                                    document.body.appendChild(dot);
                                    """
                                )

                            except Exception as e:
                                print(e)
                            finally:
                                page.evaluate(
                                    """
                                    const dots = document.querySelectorAll('.showdot');
                                    dots.forEach(dot => dot.remove());
                                    """
                                )


with sync_playwright() as playwright:
    run1(playwright)
