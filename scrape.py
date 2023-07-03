import asyncio
from pyppeteer import launch

async def scrape_page(url):
    browser = await launch(headless=False)
    page = await browser.newPage()
    await page.goto(url)

    # Select the option with value "04" (5) in the <select> element
    await page.select('#ctl00_cphMain_SearchAdvanced1_ddlStZaposlenihOd', '04')

    # Click the search button
    await asyncio.sleep(10)  # Add a delay of 10 seconds
    await page.evaluate('document.getElementById("ctl00_cphMain_SearchAdvanced1_btnPoisciPodjetja").click()')

    current_page = 1
    has_next_page = True

    while has_next_page:
        print(f'Page {current_page}')

        await page.waitForSelector('.b-search-results .b-table .b-table-row .b-table-cell-title a.b-link-company')
        search_result_items = await page.querySelectorAll('.b-search-results .b-table .b-table-row .b-table-cell-title a.b-link-company')

        for item in search_result_items:
            item_text = await page.evaluate('(element) => element.textContent', item)
            print('Search Result Item:', item_text)

            # Click on the search result
            await item.click()
            await page.waitForNavigation(timeout=20000)  # Set a timeout of 20 seconds for navigation

            # Extract information from the loaded website
            title = await page.evaluate('document.querySelector(".col.b-title h1").textContent.trim()')
            address = await page.evaluate('document.querySelector(".b-box-body .i-ostalo-lokacija").textContent.trim()')
            phone_number = await page.evaluate('document.querySelector(".b-box-body .i-ostalo-telefon").textContent.trim()')
            website = await page.evaluate('document.querySelector(".b-box-body a.i-ostalo-link").textContent.trim()')
            email = await page.evaluate('document.querySelector(".b-box-body .i-orodja-ovojnice").getAttribute("href").replace("mailto:", "")')
            number_of_employees = await page.evaluate('document.querySelector(".b-attr-group-list .b-attr-group:nth-child(4) .b-attr-value").textContent.trim()')
            tsmedia_activity = await page.evaluate('document.querySelector(".b-attr-group-list .b-attr-group:nth-child(6) .b-attr-value").textContent.trim()')

            print('Title:', title)
            print('Address:', address)
            print('Phone Number:', phone_number)
            print('Website:', website)
            print('Email:', email)
            print('Number of Employees:', number_of_employees)
            print('TS Media Activity:', tsmedia_activity)

            # Go back to the search results page
            await page.goBack()
            await page.waitForNavigation(timeout=20000)  # Set a timeout of 20 seconds for navigation
            await asyncio.sleep(2)

        # Check if there is a next page
        has_next_page = await page.evaluate('''() => {
            const nextPageButton = document.querySelector('.b-search-pager a.b-page-link:not(.aspNetDisabled)');
            if (nextPageButton) {
                nextPageButton.click();
                return true;
            }
            return false;
        }''')

        current_page += 1
        if has_next_page:
            # Reload the search results page
            await page.reload()
            await page.waitForNavigation(timeout=20000)  # Set a timeout of 20 seconds for navigation
            await asyncio.sleep(2)

    # Close the browser
    await browser.close()

url = 'https://www.bizi.si/iskanje/'

# Run the scraping function
asyncio.get_event_loop().run_until_complete(scrape_page(url))
