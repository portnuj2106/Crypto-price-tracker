from playwright.async_api import async_playwright

from playwright.async_api import TimeoutError


async def scrape_prices(currency: str):
    try:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=False)
            page = await browser.new_page()
            await page.goto("https://coinmarketcap.com/")

            for _ in range(15):
                await page.mouse.wheel(0, 2000)
                await page.wait_for_timeout(1000)

            trx_xpath = "//table[@class='sc-14cb040a-3 dsflYb cmc-table  ']/tbody/tr"
            trs_list = await page.query_selector_all(trx_xpath)

            master_list = []
            for tr in trs_list:
                coin_dict = {}

                tds = await tr.query_selector_all("//td")
                name = await tds[2].query_selector("//p[@color='text']")
                price = await tds[3].inner_text()
                symbol = await tds[2].query_selector("//p[@color='text3']")

                coin_dict["id"] = await tds[1].inner_text()
                coin_dict["Name"] = await name.inner_text()
                coin_dict["Symbol"] = await symbol.inner_text()

                coin_dict["Price"] = float(price.replace("$", '').replace(',', ''))

                if str(coin_dict["Symbol"]) in currency.upper():
                    master_list.append(coin_dict)

            await browser.close()
            return master_list
    except TimeoutError:
        print("Timeout error occurred while scraping prices.")
        return None
