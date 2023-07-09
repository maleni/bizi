import asyncio
import random
import string
import pandas as pd
import os
from pyppeteer import launch
from pyppeteer.errors import NetworkError

# Generate a random user agent string
def generate_user_agent():
    # List of common user agents
    user_agents = [
        # Add your desired user agent strings here
        # Example user agents:
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0',
    ]
    return random.choice(user_agents)


async def scrape_page(url):
    browser = await launch(
        headless=False,
        args=[
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--disable-setuid-sandbox',
            '--no-first-run',
            '--no-sandbox',
            '--no-zygote',
            '--deterministic-fetch',
            '--disable-features=IsolateOrigins',
            '--disable-site-isolation-trials',
            # '--single-process',
        ],
    )
    page = await browser.newPage()

    # Set user agent header
    user_agent = generate_user_agent()
    await page.setUserAgent(user_agent)

    options = {"waitUntil": 'load', "timeout": 1000000}
    await page.goto(url, options=options)

    # Select the option with value "04" (5) in the <select> element
    await page.select('#ctl00_cphMain_SearchAdvanced1_ddlStZaposlenihOd', '04')

    # Click the search button
    await asyncio.sleep(30)  # Add a delay of 10 seconds
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
                options = {"waitUntil": 'load', "timeout": 1000000}
                await new_page.goto(href, options=options)

                # Extract information from the loaded website
                try:
                    title = await new_page.evaluate('document.querySelector(".col.b-title h1").textContent.trim()')
                except Exception as e:
                    title = ""

                try:
                    address = await new_page.evaluate('document.querySelector(".b-box-body .i-ostalo-lokacija").textContent.trim()')
                except Exception as e:
                    address = ""

                try:
                    phone_number = await new_page.evaluate('document.querySelector(".b-box-body .i-ostalo-telefon").textContent.trim()')
                except Exception as e:
                    phone_number = ""

                try:
                    website = await new_page.evaluate('document.querySelector(".b-box-body a.i-ostalo-link").textContent.trim()')
                except Exception as e:
                    website = ""

                try:
                    email = await new_page.evaluate('document.querySelector(".b-box-body .i-orodja-ovojnice").getAttribute("href").replace("mailto:", "")')
                except Exception as e:
                    email = ""

                try:
                    number_of_employees = await new_page.evaluate('document.querySelector(".b-attr-group-list .b-attr-group:nth-child(4) .b-attr-value").textContent.trim()')
                except Exception as e:
                    number_of_employees = ""

                try:
                    tsmedia_activity = await new_page.evaluate('document.querySelector(".b-attr-group-list .b-attr-group:nth-child(6) .b-attr-value").textContent.trim()')
                except Exception as e:
                    tsmedia_activity = ""

                result = {
                    'Title': title,
                    'Address': address,
                    'Phone Number': phone_number,
                    'Website': website,
                    'Email': email,
                    'Number of Employees': number_of_employees,
                    'TS Media Activity': tsmedia_activity
                }
                print(f'Result: {result}')

                results.append(result)

                # Close the new tab
                await new_page.close()

                # Go back to the search results page
                try:
                    await page.bringToFront()
                except NetworkError:
                    pass

            # Check if there is a next page
            await asyncio.sleep(35)
            next_page_button = await page.querySelector('#divResultsPagerTop .b-page-link.b-active')
            if next_page_button is None:
                break

            # Get the next page button by finding the next sibling of the active page button
            next_page_button = await page.evaluateHandle('(a) => a.nextElementSibling', next_page_button)

            # Click the next page button
            await asyncio.sleep(35)  # Add a delay before navigating to the next page
            current_page += 1
            await next_page_button.click()

    except Exception as e:
        print(f'Error occurred: {e}')

    finally:
        print('close all')
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
