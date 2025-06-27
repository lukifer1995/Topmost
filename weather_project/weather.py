import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re, random

URL = r"https://www.msn.com/vi-vn/weather/forecast/in-Qu%E1%BA%ADn-9,H%E1%BB%93-Ch%C3%AD-Minh?loc=eyJsIjoiUXXhuq1uIDkiLCJyIjoiSOG7kyBDaMOtIE1pbmgiLCJjIjoiVmnhu4d0IE5hbSIsImkiOiJWTiIsImciOiJ2aS12biIsIngiOiIxMDYuODE3IiwieSI6IjEwLjgzMDMifQ%3D%3D&weadegreetype=C"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Đổi thành False nếu muốn debug
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)  # hoặc "load"

        # Chờ random 0.5–2s
        await asyncio.sleep(random.uniform(2, 3))
        await page.evaluate("window.scrollTo(500, Math.floor(document.body.scrollHeight / 7))")
        await asyncio.sleep(random.uniform(2, 3))   

        # Bấm vào button có title="Danh sách"
        await page.click('button[title="Danh sách"]')
        # await page.click('button.forecastButton-DS-EntryPoint1-2[title="Danh sách"][aria-label="Danh sách"][data-forecasttype="forecastButton_list"]')


        # Chờ random nữa
        await asyncio.sleep(random.uniform(2, 3))

        # Lưu HTML sau khi đã load và tương tác xong
        content = await page.content()

        await browser.close()

    # Dùng BeautifulSoup để phân tích
    soup = BeautifulSoup(content, "lxml")

    # Tìm tất cả các div có id bắt đầu bằng 'itemContainer'
    candidates = soup.find_all("div", id=re.compile(r"^itemContainer\d+"))






    # Lọc các div chứa từ 'mưa' nhưng không chứa 'lượng mưa'
    selected_divs = [
        div for div in candidates
        if re.search(r'mưa', div.get_text(strip=True), flags=re.IGNORECASE)
        and not re.search(r'lượng\s+mưa', div.get_text(strip=True), flags=re.IGNORECASE)
    ]

    if selected_divs:
        # Lưu div đầu tiên thỏa mãn
        html_output = f"""
        <html>
            <head><meta charset="utf-8"></head>
            <body>{str(selected_divs[0])}</body>
        </html>
        """
        with open("output_mua_rao.html", "w", encoding="utf-8") as f:
            f.write(html_output)
        print("✅ Đã lưu ra output_mua_rao.html")
    else:
        # Không tìm được -> xuất tất cả div itemContainer để debug
        with open("output_debug_all_itemContainers.html", "w", encoding="utf-8") as f:
            f.write("<html><head><meta charset='utf-8'></head><body>")
            for div in candidates:
                f.write(str(div))
            f.write("</body></html>")
        print("⚠️ Không tìm thấy div chứa từ 'mưa' phù hợp — đã lưu tất cả vào output_debug_all_itemContainers.html")


# Chạy hàm main
asyncio.run(main())
