from playwright_pass_cloudflare import *


async def bypass_cloudflare_async(browser, url: str, max_time: int) -> None:
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(url)
    start_time = time.time()
    while True:
        try:
            await page.wait_for_load_state("domcontentloaded")
            html = await page.content()
            if is_page_unblocked(html):
                soup = BeautifulSoup(pure_html_remove_css_and_js(html), "html.parser")
                htm_plaintext = soup.select_one("html").text
                print(htm_plaintext)
                print("[green]Page is unblocked[/green]")
                await context.storage_state(path=state_path)
                break
            else:
                print("[red]Blocked by cloudflare[/red]")
                print(f"current url: {page.url}")
            div_element = await page.query_selector("#kGtPC2 > div > div")
            if div_element:
                print("security check div_element found")
                bounding_box = await div_element.bounding_box()
                if bounding_box:
                    width = bounding_box["width"]
                    height = bounding_box["height"]
                    if width > 0 and height > 0:
                        print("security check div_element width and height > 0, loaded")
                        await div_element.screenshot(path=div_screenshot_path)
                        print(f"div_screenshot_path: {div_screenshot_path}")
                        await page.wait_for_timeout(random.randint(500, 1000))
                        square_template = cv2.imread(
                            template_path, cv2.IMREAD_GRAYSCALE
                        )
                        remove_right_white_background(
                            div_screenshot_path, div_screenshot_no_white_path
                        )
                        print(
                            f"div_screenshot_no_white_path: {div_screenshot_no_white_path}"
                        )
                        div_screenshot = cv2.imread(
                            div_screenshot_no_white_path, cv2.IMREAD_GRAYSCALE
                        )
                        result = cv2.matchTemplate(
                            div_screenshot, square_template, cv2.TM_CCOEFF_NORMED
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
                                full_screen_shot, div_screenshot, cv2.TM_CCOEFF_NORMED
                            )
                            threshold = 0.6
                            loc_screen = np.where(result >= threshold)
                            if len(loc_screen[0]) > 2:
                                print("security check div_element found in screen")
                                average_loc_divIn_screen = np.mean(loc_screen, axis=1)
                                screen_x = average_loc_divIn_screen[0]
                                screen_y = average_loc_divIn_screen[1]
                                result_x = (
                                    screen_x
                                    + average_loc_squareIn_div[0]
                                    + square_template.shape[0] // 6
                                )
                                result_y = (
                                    screen_y
                                    + average_loc_squareIn_div[1]
                                    + square_template.shape[1] // 3
                                )
                                result_x, result_y = result_y, result_x
                                print(
                                    f"caculated result_x: {result_x}, result_y: {result_y}"
                                )
                                pyautogui.click(
                                    x=result_x,
                                    y=result_y,
                                    duration=random.uniform(0.1, 0.3),
                                )
                                print("click success")

            await asyncio.sleep(1)
            if time.time() - start_time > max_time:
                print("[red]Max time exceeded[/red]")
                break
        except Exception as e:
            print(f"Error: {e}")
            await page.reload()
            await page.wait_for_load_state("domcontentloaded")
    # html = await page.content()
    # soup = BeautifulSoup(pure_html_remove_css_and_js(html), "html.parser")
    # htm_plaintext = soup.select_one("html").text
    # print(htm_plaintext)
    # print("[green]Page is unblocked[/green]")
    # await context.storage_state(path=state_path)
    # break
