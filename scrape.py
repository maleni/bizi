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
    
    async def scrape_page(self, url, max_pages=None):
        async with async_playwright() as p:
            # Use different browsers randomly
            browser_type = random.choice([p.chromium, p.firefox])
            browser = await browser_type.launch(
                headless=False  # Set to True for production
                # args removed for debugging
            )
            
            context = await self.setup_stealth_context(browser)
            page = await context.new_page()
            
            # Set longer timeout for slow connections
            page.set_default_timeout(60000)
            
            try:
                print(f"Navigating to: {url}")
                await page.goto(url, wait_until='domcontentloaded')
                await self.random_delay(3, 6)  # Initial delay
                
                # Wait for company list
                try:
                    await page.wait_for_selector('.b-table-cell-title a.b-link-company', timeout=20000)
                    print("Company list loaded successfully.")
                except TimeoutError:
                    print("Timeout waiting for company list")
                    await page.screenshot(path='error_screenshot.png')
                    return []
                
                current_page = 1
                all_results = []
                
                while True:
                    if max_pages and current_page > max_pages:
                        print(f"Reached maximum pages limit: {max_pages}")
                        break
                        
                    print(f'Scraping page {current_page}...')
                    
                    # Get company URLs from current page
                    company_urls = await page.evaluate('''() => {
                        const urls = [];
                        const links = document.querySelectorAll('.b-table-cell-title a.b-link-company');
                        links.forEach(link => {
                            if (link.href) urls.push(link.href);
                        });
                        return urls;
                    }''')
                    
                    print(f"Found {len(company_urls)} companies on page {current_page}")
                    print(f"Extracted company URLs: {company_urls}")
                    
                    # Process each company
                    for i, company_url in enumerate(company_urls):
                        print(f"Processing company {i+1}/{len(company_urls)}: {company_url}")

                        # Validate URL before navigation
                        if not (isinstance(company_url, str) and company_url.startswith("http")):
                            print(f"Skipping invalid URL: {company_url}")
                            continue
                        
                        # Create new tab for each company
                        company_page = await context.new_page()
                        company_data = await self.extract_company_data(company_page, company_url)
                        await company_page.close()
                        
                        if company_data:
                            all_results.append(company_data)
                            print(f"Scraped: {company_data['Title']}")
                        
                        # Random delay between companies
                        await self.random_delay(2, 4)
                    
                    # Save progress after each page
                    if all_results:
                        df = pd.DataFrame(all_results)
                        df.to_excel(f'scraped_data_page_{current_page}.xlsx', index=False)
                        print(f"Saved {len(all_results)} results so far")
                    
                    # Check for next page with multiple strategies
                    print("Looking for next page...")
                    
                    # Strategy 1: Look for specific page number
                    next_page_num = current_page + 1
                    next_page_selectors = [
                        f'#ctl00_cphMain_ResultsPager_repPager a.b-page-link:has-text("{next_page_num}")',
                        f'a.b-page-link:has-text("{next_page_num}")',
                        f'a[href*="page={next_page_num}"]',
                        f'a:has-text("{next_page_num}")'
                    ]
                    
                    next_page_link = None
                    for selector in next_page_selectors:
                        try:
                            next_page_link = await page.query_selector(selector)
                            if next_page_link:
                                print(f"Found next page link with selector: {selector}")
                                break
                        except:
                            continue
                    
                    # Strategy 2: Look for "Next" button or arrow
                    if not next_page_link:
                        next_button_selectors = [
                            'a.b-page-link:has-text(">")',
                            'a:has-text("Next")',
                            'a:has-text("Naprej")',  # Slovenian for "Next"
                            '.pagination a:last-child',
                            'a[title*="next"]',
                            'a[title*="naprej"]'
                        ]
                        
                        for selector in next_button_selectors:
                            try:
                                next_page_link = await page.query_selector(selector)
                                if next_page_link:
                                    print(f"Found next button with selector: {selector}")
                                    break
                            except:
                                continue
                    
                    # Strategy 3: Debug pagination structure
                    if not next_page_link:
                        print("Debugging pagination structure...")
                        pagination_info = await page.evaluate('''() => {
                            const pagination = document.querySelector('#ctl00_cphMain_ResultsPager_repPager') || 
                                              document.querySelector('.pagination') ||
                                              document.querySelector('[class*="pager"]');
                            
                            if (pagination) {
                                const links = pagination.querySelectorAll('a');
                                const linkInfo = Array.from(links).map(link => ({
                                    text: link.textContent.trim(),
                                    href: link.href,
                                    className: link.className
                                }));
                                return {
                                    found: true,
                                    innerHTML: pagination.innerHTML,
                                    links: linkInfo
                                };
                            }
                            return { found: false };
                        }''')
                        
                        print(f"Pagination debug info: {pagination_info}")
                        
                        # Try to find any link that might be next page
                        if pagination_info.get('found'):
                            potential_next = await page.evaluate(f'''() => {{
                                const links = document.querySelectorAll('#ctl00_cphMain_ResultsPager_repPager a, .pagination a, [class*="pager"] a');
                                for (let link of links) {{
                                    const text = link.textContent.trim();
                                    if (text === "{next_page_num}" || text === ">" || text.toLowerCase().includes("next") || text.toLowerCase().includes("naprej")) {{
                                        return {{ text: text, href: link.href, found: true }};
                                    }}
                                }}
                                return {{ found: false }};
                            }}''')
                            
                            if potential_next.get('found'):
                                next_page_link = await page.query_selector(f'a[href="{potential_next["href"]}"]')
                                print(f"Found potential next page: {potential_next}")
                    
                    if not next_page_link:
                        print("No more pages found - pagination exhausted")
                        break
                    
                    print(f"Navigating to page {current_page + 1}...")
                    
                    # Click with better error handling
                    try:
                        await next_page_link.scroll_into_view_if_needed()
                        await self.random_delay(1, 2)
                        await next_page_link.click()
                        await page.wait_for_load_state('domcontentloaded', timeout=30000)
                        await self.random_delay(3, 6)
                        
                        # Verify we actually moved to next page
                        new_url = page.url
                        print(f"New URL after navigation: {new_url}")
                        
                    except Exception as e:
                        print(f"Error clicking next page: {e}")
                        break
                    
                    current_page += 1
                
                # Save final results
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
    url = 'https://www.bizi.si/TSMEDIA/A/avtoservis-380/'
    
    # Limit to 3 pages for testing - remove max_pages parameter for full scrape
    results = await scraper.scrape_page(url, max_pages=3)
    print(f"Scraping finished with {len(results)} total results")

if __name__ == "__main__":
    asyncio.run(main())
