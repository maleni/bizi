import asyncio
from pyppeteer import launch
from pyppeteer.errors import NetworkError
import pandas as pd
import os

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
    results = []

    try:
        while True:
            print(f'Page {current_page}')

            await page.waitForSelector('.b-table-cell-title a.b-link-company')
            search_result_items = await page.evaluate('''() => {
                const results = [];
                const items = document.querySelectorAll('.b-table-row .b-table-cell-title a.b-link-company, .b-table-cell-title div.b-link-company');
                for (let i = 0; i < items.length; i++) {
                    const item = items[i];
                    const href = item.href;
                    results.push(href);
                }
                return results;
            }''')

            

            for href in search_result_items:
                # Open the search result in a new tab
                new_page = await browser.newPage()
                await new_page.evaluateOnNewDocument('window.open = function() {};')
                await new_page.goto(href)

                # Extract information from the loaded website
                title = await new_page.evaluate('document.querySelector(".col.b-title h1").textContent.trim()')
                address = await new_page.evaluate('document.querySelector(".b-box-body .i-ostalo-lokacija").textContent.trim()')
                phone_number = await new_page.evaluate('document.querySelector(".b-box-body .i-ostalo-telefon").textContent.trim()')
                website = await new_page.evaluate('document.querySelector(".b-box-body a.i-ostalo-link").textContent.trim()')
                email = await new_page.evaluate('document.querySelector(".b-box-body .i-orodja-ovojnice").getAttribute("href").replace("mailto:", "")')
                number_of_employees = await new_page.evaluate('document.querySelector(".b-attr-group-list .b-attr-group:nth-child(4) .b-attr-value").textContent.trim()')
                tsmedia_activity = await new_page.evaluate('document.querySelector(".b-attr-group-list .b-attr-group:nth-child(6) .b-attr-value").textContent.trim()')

                result = {
                    'Title': title,
                    'Address': address,
                    'Phone Number': phone_number,
                    'Website': website,
                    'Email': email,
                    'Number of Employees': number_of_employees,
                    'TS Media Activity': tsmedia_activity
                }

                results.append(result)

                # Close the new tab
                await new_page.close()

                # Go back to the search results page
                try:
                    await page.bringToFront()
                except NetworkError:
                    pass

                # Check if there is a next page
            next_page_button = await page.querySelector('#divResultsPagerTop .b-page-link.b-active')
            if next_page_button is None:
                break

            # Get the next page button by finding the next sibling of the active page button
            next_page_button = await page.evaluateHandle('(a) => a.nextElementSibling', next_page_button)

            # Click the next page button
            await asyncio.sleep(3)  # Add a delay before navigating to the next page
            await next_page_button.click()

    except Exception as e:
        print(f'Error occurred: {e}')

    finally:
        # Convert results to a DataFrame
        df = pd.DataFrame(results)

        # Save DataFrame to Excel
        df.to_excel('scraped_data.xlsx', index=False)

        # Close the browser
        await browser.close()

        # Delete temporary user data directory
        user_data_dir = browser.userDataDir
        await browser.disconnect()
        await browser.process.communicate()
        await browser.close()
        await asyncio.sleep(1)
        if os.path.exists(user_data_dir):
            os.remove(user_data_dir)

url = 'https://www.bizi.si/iskanje/'
asyncio.get_event_loop().run_until_complete(scrape_page(url))
