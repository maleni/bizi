import asyncio
import random
import pandas as pd
import time
from playwright.async_api import async_playwright, TimeoutError

class StealthScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    def get_random_user_agent(self):
        return random.choice(self.user_agents)

    async def handle_cookie_popup(self, page):
        """
        Detect and dismiss the Didomi cookie popup if present.
        Tries to click the 'Sprejmi vse' (Accept all) or close button.
        """
        try:
            # Wait for the popup to appear (short timeout)
            popup_selector = '#didomi-popup'
            accept_btn_selectors = [
                'button.didomi-continue-without-agreeing',  # Sometimes present
                'button.didomi-accept-all-button',          # Most common
                'button[aria-label*="Sprejmi"]',            # Slovenian
                'button:has-text("Sprejmi vse")',
                'button:has-text("Sprejmi")',
                'button:has-text("Accept all")',
                'button:has-text("Agree")',
                '.didomi-popup__button'                     # Fallback
            ]
            popup = await page.query_selector(popup_selector)
            if popup:
                for btn_selector in accept_btn_selectors:
                    try:
                        btn = await page.query_selector(btn_selector)
                        if btn:
                            await btn.click()
                            print("Cookie popup dismissed.")
                            await asyncio.sleep(1)
                            break
                    except Exception:
                        continue
        except Exception:
            pass
    
    def get_random_viewport(self):
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1600, 'height': 900},
            {'width': 1280, 'height': 720}
        ]
        return random.choice(viewports)
    
    async def random_delay(self, min_seconds=2, max_seconds=5):
        """Add random delay between actions"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def human_like_scroll(self, page):
        """Simulate human-like scrolling behavior"""
        await page.evaluate('''() => {
            return new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 100;
                const timer = setInterval(() => {
                    const scrollHeight = document.body.scrollHeight;
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    
                    if(totalHeight >= scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            });
        }''')
    
    async def setup_stealth_context(self, browser):
        """Setup context with stealth features"""
        context = await browser.new_context(
            viewport=self.get_random_viewport(),
            user_agent=self.get_random_user_agent(),
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
        )
        
        # Add stealth scripts to avoid detection
        await context.add_init_script("""
            // Override the navigator.webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock languages and plugins
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        return context
    
    async def extract_company_data(self, page, url):
        """Extract company data from individual page"""
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await self.random_delay(1, 3)
            
            # Wait for content to load
            try:
                await page.wait_for_selector('.col.b-title h1', timeout=10000)
            except TimeoutError:
                print(f"Content not loaded for {url}")
                return None
            
            # Simulate human behavior
            await self.human_like_scroll(page)
            await self.random_delay(1, 2)
            
            # Extract data with better error handling and debugging
            data = await page.evaluate('''() => {
                const getData = (selector, attribute = 'textContent') => {
                    try {
                        const element = document.querySelector(selector);
                        if (!element) {
                            console.log(`Element not found for selector: ${selector}`);
                            return '';
                        }
                        
                        if (attribute === 'textContent') {
                            return element.textContent.trim();
                        } else if (attribute === 'href') {
                            const href = element.getAttribute('href') || '';
                            return href;
                        }
                        return element.getAttribute(attribute) || '';
                    } catch (e) {
                        console.log(`Error getting data for selector ${selector}:`, e);
                        return '';
                    }
                };
                
                // Try multiple selectors for phone and email
                const getPhone = () => {
                    const selectors = [
                        '.b-box-body .i-ostalo-telefon',
                        '.i-ostalo-telefon',
                        '[class*="telefon"]',
                        '.b-contact-info .phone',
                        'a[href^="tel:"]'
                    ];
                    for (let selector of selectors) {
                        const result = getData(selector);
                        if (result) return result;
                        
                        // Try href attribute for tel: links
                        const element = document.querySelector(selector);
                        if (element && element.href && element.href.startsWith('tel:')) {
                            return element.href.replace('tel:', '');
                        }
                    }
                    return '';
                };
                
                const getEmail = () => {
                    const selectors = [
                        '.b-box-body .i-orodja-ovojnice',
                        '.i-orodja-ovojnice',
                        '[class*="ovojnice"]',
                        'a[href^="mailto:"]',
                        '.b-contact-info .email'
                    ];
                    for (let selector of selectors) {
                        const element = document.querySelector(selector);
                        if (element && element.href && element.href.startsWith('mailto:')) {
                            return element.href.replace('mailto:', '');
                        }
                        const result = getData(selector);
                        if (result && result.includes('@')) return result;
                    }
                    return '';
                };
                
                return {
                    title: getData('.col.b-title h1') || getData('h1') || getData('.title'),
                    address: getData('.b-box-body .i-ostalo-lokacija') || getData('.i-ostalo-lokacija') || getData('[class*="lokacija"]'),
                    phone: getPhone(),
                    website: getData('.b-box-body a.i-ostalo-link') || getData('a.i-ostalo-link') || getData('a[href^="http"]'),
                    email: getEmail(),
                    employees: getData('.b-attr-group-list .b-attr-group:nth-child(4) .b-attr-value'),
                    registration_date: getData('.b-attr-group-list .b-attr-group:nth-child(5) .b-attr-value'),
                    activity: getData('.b-attr-group-list .b-attr-group:nth-child(6) .b-attr-value')
                };
            }''')
            
            return {
                'Title': data['title'],
                'Address': data['address'],
                'Phone Number': data['phone'],
                'Website': data['website'],
                'Email': data['email'],
                'Number of Employees': data['employees'],
                'Registration date': data['registration_date'],
                'TS Media Activity': data['activity'],
                'URL': url
            }
            
        except Exception as e:
            print(f"Error extracting data from {url}: {e}")
            return None
    
    async def scrape_page(self, url, start_page=1, max_pages=None):
        async with async_playwright() as p:
            browser_type = random.choice([p.chromium, p.firefox])
            browser = await browser_type.launch(headless=False)  # Set to True for production
            context = await self.setup_stealth_context(browser)
            page = await context.new_page()
            page.set_default_timeout(60000)
            
            try:
                print(f"Navigating to: {url}")
                await page.goto(url, wait_until='domcontentloaded')
                await self.random_delay(3, 6)

                # Handle cookie popup if present
                await self.handle_cookie_popup(page)
                
                # Wait for company list
                await page.wait_for_selector('.b-table-cell-title a.b-link-company', timeout=20000)
                print("Company list loaded successfully.")
                
                current_page = 1
                all_results = []
                
                # Helper function to find the next page link
                async def find_next_page_link(page, current_page):
                    next_page_num = current_page + 1
                    next_page_selectors = [
                        f'#ctl00_cphMain_ResultsPager_repPager a.b-page-link:has-text("{next_page_num}")',
                        f'a.b-page-link:has-text("{next_page_num}")',
                        f'a[href*="page={next_page_num}"]',
                        f'a:has-text("{next_page_num}")'
                    ]
                    for selector in next_page_selectors:
                        try:
                            link = await page.query_selector(selector)
                            if link:
                                print(f"Found next page link with selector: {selector}")
                                return link
                        except:
                            continue
                    
                    next_button_selectors = [
                        'a.b-page-link:has-text(">")',
                        'a:has-text("Next")',
                        'a:has-text("Naprej")',
                        '.pagination a:last-child',
                        'a[title*="next"]',
                        'a[title*="naprej"]'
                    ]
                    for selector in next_button_selectors:
                        try:
                            link = await page.query_selector(selector)
                            if link:
                                print(f"Found next button with selector: {selector}")
                                return link
                        except:
                            continue
                    return None
                
                # Navigate to the starting page
                while current_page < start_page:
                    next_page_link = await find_next_page_link(page, current_page)
                    if not next_page_link:
                        print(f"Cannot navigate to page {start_page} - next page link not found")
                        await browser.close()
                        return all_results
                    print(f"Navigating to page {current_page + 1} to reach start_page {start_page}")
                    await next_page_link.scroll_into_view_if_needed()
                    await next_page_link.click()
                    await page.wait_for_load_state('domcontentloaded', timeout=30000)
                    await self.random_delay(3, 6)
                    # Handle cookie popup if it reappears
                    await self.handle_cookie_popup(page)
                    current_page += 1
                
                # Main scraping loop starting from start_page
                while True:
                    if max_pages and current_page > max_pages:
                        print(f"Reached maximum pages limit: {max_pages}")
                        break
                    
                    print(f'Scraping page {current_page}...')
                    company_urls = await page.evaluate('''() => {
                        const urls = [];
                        const links = document.querySelectorAll('.b-table-cell-title a.b-link-company');
                        links.forEach(link => {
                            if (link.href) urls.push(link.href);
                        });
                        return urls;
                    }''')
                    print(f"Found {len(company_urls)} companies on page {current_page}")

                    # If no companies found, stop scraping (end of real results)
                    if len(company_urls) == 0:
                        print("No companies found on this page. Stopping pagination.")
                        break

                    for i, company_url in enumerate(company_urls):
                        if not (isinstance(company_url, str) and company_url.startswith("http")):
                            print(f"Skipping invalid URL: {company_url}")
                            continue
                        company_page = await context.new_page()
                        company_data = await self.extract_company_data(company_page, company_url)
                        await company_page.close()
                        if company_data:
                            all_results.append(company_data)
                            print(f"Scraped: {company_data['Title']}")
                        await self.random_delay(2, 4)

                    if all_results:
                        df = pd.DataFrame(all_results)
                        df.to_excel(f'scraped_data_page_{current_page}.xlsx', index=False)
                        print(f"Saved {len(all_results)} results so far")

                    next_page_link = await find_next_page_link(page, current_page)
                    if not next_page_link:
                        print("No more pages found - pagination exhausted")
                        break
                    
                    print(f"Navigating to page {current_page + 1}...")
                    await next_page_link.scroll_into_view_if_needed()
                    await next_page_link.click()
                    await page.wait_for_load_state('domcontentloaded', timeout=30000)
                    await self.random_delay(3, 6)
                    # Handle cookie popup if it reappears
                    await self.handle_cookie_popup(page)
                    current_page += 1
                
                if all_results:
                    df = pd.DataFrame(all_results)
                    df.to_excel('final_scraped_data.xlsx', index=False)
                    print(f'Scraping completed! Total results: {len(all_results)}')
                
                return all_results
                
            except Exception as e:
                print(f"Error during scraping: {e}")
                await page.screenshot(path='error_final_screenshot.png')
                return []
            
            finally:
                await browser.close()

# Usage
async def main():
    scraper = StealthScraper()
    url = 'https://www.bizi.si/TSMEDIA/F/frizerska-dejavnost-1260/'
    results = await scraper.scrape_page(url, start_page=0)  # Start from page 35
    print(f"Scraping finished with {len(results)} total results")

if __name__ == "__main__":
    asyncio.run(main())
