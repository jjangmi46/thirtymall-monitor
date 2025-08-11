#!/usr/bin/env python3
"""
ThirtyMall Product Monitor - Selenium Version
Monitors for new products containing '버터' in category 796224
Uses headless browser to handle JavaScript-loaded content
"""

import json
import os
import time
import random
from datetime import datetime
import hashlib
import requests

# Try to import selenium, fall back to requests if not available
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not available, falling back to requests method")

def get_products_selenium(url):
    """Scrape products using Selenium (handles JavaScript)"""
    if not SELENIUM_AVAILABLE:
        print("Selenium not installed, cannot handle JavaScript content")
        return []
    
    driver = None
    try:
        # Configure Chrome options for GitHub Actions
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebDriver/537.36')
        chrome_options.add_argument('--accept-lang=ko-KR,ko,en')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        print("Starting Chrome browser...")
        
        # Set timeouts
        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError("Chrome startup timeout")
        
        # 30 second timeout for Chrome startup
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            signal.alarm(0)  # Cancel timeout
            print("Chrome browser started successfully")
        except:
            signal.alarm(0)  # Cancel timeout
            raise
        
        # Set page load timeout
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(5)
        
        print(f"Loading page: {url}")
        
        # Load page with timeout handling
        try:
            driver.get(url)
            print("Page loaded successfully")
        except Exception as e:
            print(f"Page load failed: {e}")
            # Try one more time
            print("Retrying page load...")
            time.sleep(2)
            driver.get(url)
        
        # Wait for page to load
        print("Waiting for page to stabilize...")
        time.sleep(5)
        
        # Check if page loaded properly
        current_url = driver.current_url
        page_title = driver.title
        print(f"Current URL: {current_url}")
        print(f"Page title: {page_title}")
        
        # Wait for products to load - with timeout
        try:
            print("Waiting for products to load...")
            WebDriverWait(driver, 10).until(
                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "a[href*='product'], a[href*='goods'], a[href*='/p/']")) > 0
                or "버터" in driver.page_source
                or len(driver.page_source) > 50000  # Page has substantial content
            )
            print("Content loaded successfully")
        except TimeoutException:
            print("Timeout waiting for content - proceeding anyway")
        
        # Additional wait to ensure all dynamic content is loaded
        time.sleep(3)
        
        # Save page source for debugging
        try:
            page_source = driver.page_source
            with open('debug_selenium_page.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"Saved Selenium page HTML ({len(page_source)} chars)")
            
            # Quick check if we have the right content
            if '버터' in page_source:
                print("✓ Found '버터' in page source")
            else:
                print("✗ No '버터' found in page source")
                
        except Exception as e:
            print(f"Error saving page source: {e}")
        
        # Search for products containing '버터'
        products = []
        
        # Method 1: Look for elements containing '버터' text
        butter_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '버터')]")
        print(f"Found {len(butter_elements)} elements containing '버터'")
        
        processed_links = set()
        
        for element in butter_elements:
            try:
                # Get the text content
                title = element.text.strip()
                if not title or '버터' not in title:
                    continue
                
                # Find the nearest link (parent or child)
                link_element = None
                product_container = None
                
                # Check if element itself is a link
                if element.tag_name == 'a':
                    link_element = element
                    product_container = element
                else:
                    # Look for link in parent elements
                    parent = element
                    for _ in range(5):  # Check up to 5 levels up
                        parent = parent.find_element(By.XPATH, "..")
                        if parent.tag_name == 'a':
                            link_element = parent
                            product_container = parent
                            break
                        # Or look for a link within the parent
                        links = parent.find_elements(By.TAG_NAME, 'a')
                        if links:
                            link_element = links[0]
                            product_container = parent
                            break
                
                link = ""
                if link_element:
                    link = link_element.get_attribute('href') or ""
                    
                    # Skip if we've already processed this link
                    if link in processed_links:
                        continue
                    processed_links.add(link)
                
                # Look for price in the product container or nearby elements
                price = ""
                if product_container:
                    # Common price selectors for Korean e-commerce
                    price_selectors = [
                        '.price', '.cost', '.amount', '.won',
                        '[class*="price"]', '[class*="cost"]', '[class*="won"]',
                        '.sale-price', '.current-price', '.final-price'
                    ]
                    
                    for price_sel in price_selectors:
                        try:
                            price_elem = product_container.find_element(By.CSS_SELECTOR, price_sel)
                            price_text = price_elem.text.strip()
                            # Look for Korean won patterns
                            if any(char in price_text for char in ['원', '₩', ',']):
                                price = price_text
                                break
                        except:
                            continue
                    
                    # If no price found with selectors, look for text with 원 or ₩
                    if not price:
                        container_text = product_container.text
                        import re
                        price_patterns = [
                            r'[\d,]+원',  # 1,000원
                            r'₩[\d,]+',   # ₩1,000
                            r'[\d,]+\s*원',  # 1,000 원
                        ]
                        for pattern in price_patterns:
                            matches = re.findall(pattern, container_text)
                            if matches:
                                price = matches[0]
                                break
                
                # Clean up title and price
                title = ' '.join(title.split())[:200]
                price = ' '.join(price.split()) if price else ""
                
                # Create unique ID
                product_id = hashlib.md5((title + link).encode()).hexdigest()[:8]
                
                product = {
                    'id': product_id,
                    'title': title,
                    'price': price,
                    'link': link,
                    'found_at': datetime.now().isoformat()
                }
                
                products.append(product)
                print(f"  Found product: {title[:100]} - {price}")
                
            except Exception as e:
                print(f"Error processing element: {e}")
                continue
        
        # Method 2: Look for product links and check their text
        if len(products) < 5:  # Only if we didn't find many products
            product_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='product'], a[href*='goods'], a[href*='/p/'], a[href*='item']")
            print(f"Found {len(product_links)} potential product links")
            
            for link_elem in product_links[:50]:  # Limit to avoid too much processing
                try:
                    link_text = link_elem.text.strip()
                    link_url = link_elem.get_attribute('href') or ""
                    
                    if '버터' in link_text and link_url not in processed_links:
                        processed_links.add(link_url)
                        
                        # Look for price near this link
                        price = ""
                        try:
                            # Look in parent container for price
                            parent = link_elem.find_element(By.XPATH, "..")
                            price_selectors = [
                                '.price', '.cost', '.amount', '.won',
                                '[class*="price"]', '[class*="cost"]', '[class*="won"]'
                            ]
                            
                            for price_sel in price_selectors:
                                try:
                                    price_elem = parent.find_element(By.CSS_SELECTOR, price_sel)
                                    price_text = price_elem.text.strip()
                                    if any(char in price_text for char in ['원', '₩', ',']):
                                        price = price_text
                                        break
                                except:
                                    continue
                            
                            # Fallback: look for price patterns in parent text
                            if not price:
                                import re
                                parent_text = parent.text
                                price_patterns = [r'[\d,]+원', r'₩[\d,]+', r'[\d,]+\s*원']
                                for pattern in price_patterns:
                                    matches = re.findall(pattern, parent_text)
                                    if matches:
                                        price = matches[0]
                                        break
                        except:
                            pass
                        
                        title = ' '.join(link_text.split())[:200]
                        product_id = hashlib.md5((title + link_url).encode()).hexdigest()[:8]
                        
                        product = {
                            'id': product_id,
                            'title': title,
                            'price': price,
                            'link': link_url,
                            'found_at': datetime.now().isoformat()
                        }
                        
                        products.append(product)
                        print(f"  Found product via link: {title[:100]} - {price}")
                        
                except Exception as e:
                    continue
        
        print(f"Selenium result: Found {len(products)} products with '버터'")
        return products
        
    except TimeoutError as e:
        print(f"Selenium timeout: {e}")
        return []
    except WebDriverException as e:
        print(f"Selenium WebDriver error: {e}")
        return []
    except Exception as e:
        print(f"Selenium error: {e}")
        return []
    finally:
        # Always quit the driver
        if driver:
            try:
                driver.quit()
                print("Chrome browser closed")
            except:
                pass

def get_products_requests(url):
    """Fallback method using requests (won't work for JS content)"""
    print("Using requests fallback method...")
    # Simple requests version for comparison
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open('debug_requests_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Saved requests page HTML to debug_requests_page.html")
            
            if '버터' in response.text:
                print("Found '버터' in requests response")
            else:
                print("No '버터' found in requests response")
        
        return []  # Not implementing full parsing for fallback
    except Exception as e:
        print(f"Requests fallback error: {e}")
        return []

def get_products(url):
    """Main product fetching function with multiple fallback strategies"""
    print("=== Starting product fetch ===")
    
    # Strategy 1: Try Selenium (handles JavaScript)
    if SELENIUM_AVAILABLE:
        print("Attempting Selenium method...")
        try:
            products = get_products_selenium(url)
            if products:
                print(f"✓ Selenium successful: found {len(products)} products")
                return products
            else:
                print("✗ Selenium found no products")
        except Exception as e:
            print(f"✗ Selenium failed: {e}")
    else:
        print("Selenium not available")
    
    # Strategy 2: Try requests method (fallback)
    print("Attempting requests method...")
    try:
        products = get_products_requests(url)
        if products:
            print(f"✓ Requests successful: found {len(products)} products")
            return products
        else:
            print("✗ Requests found no products")
    except Exception as e:
        print(f"✗ Requests failed: {e}")
    
    # Strategy 3: Emergency fallback - create test data if in development
    if os.getenv('GITHUB_ACTIONS'):
        print("All methods failed in GitHub Actions")
        return []
    else:
        print("All methods failed - returning empty list")
        return []

def load_previous_products():
    """Load previously found products from file"""
    try:
        with open('previous_products.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading previous products: {e}")
        return []

def save_current_products(products):
    """Save current products to file"""
    try:
        with open('previous_products.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving products: {e}")

def find_new_products(current, previous):
    """Find products that are new compared to previous scan"""
    previous_ids = {p['id'] for p in previous}
    new_products = [p for p in current if p['id'] not in previous_ids]
    return new_products

def send_telegram_notification(new_products):
    """Send notification via Telegram bot"""
    if not new_products:
        return
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("Telegram credentials not configured")
        return
    
    # Prepare message
    message = f"🧈 Found {len(new_products)} new 버터 products!\n\n"
    
    for product in new_products[:10]:
        title = product['title'][:100]
        price = product.get('price', '')
        price_text = f" - {price}" if price else ""
        message += f"• {title}{price_text}\n{product['link']}\n\n"
    
    if len(new_products) > 10:
        message += f"... and {len(new_products) - 10} more products"
    
    # Send via Telegram Bot API
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.post(telegram_url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Telegram notification sent successfully")
        else:
            print(f"Telegram notification failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")

def send_notification(new_products):
    """Send notification about new products"""
    if not new_products:
        return
    
    send_telegram_notification(new_products)
    
    print(f"\n🧈 NEW PRODUCTS FOUND ({len(new_products)}):")
    for product in new_products:
        price_text = f" - {product.get('price', '')}" if product.get('price') else ""
        print(f"  • {product['title']}{price_text}")
        print(f"    {product['link']}")
        print()

def main():
    """Main function with timeout protection"""
    import signal
    
    def timeout_handler(signum, frame):
        print("Script timeout - taking too long")
        raise TimeoutError("Script execution timeout")
    
    # Set overall script timeout (5 minutes)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)
    
    try:
        url = "https://thirtymall.com/search?q=%EB%B2%84%ED%84%B0&categoryNo=796224"
        
        print(f"Monitoring: {url}")
        print(f"Time: {datetime.now().isoformat()}")
        print(f"Selenium available: {SELENIUM_AVAILABLE}")
        print(f"Running in GitHub Actions: {bool(os.getenv('GITHUB_ACTIONS'))}")
        
        # Get current products
        current_products = get_products(url)
        
        if not current_products:
            print("No products found - this may be due to:")
            print("1. JavaScript-loaded content (need Selenium)")
            print("2. Bot detection by the website")
            print("3. Site structure changes")
            print("4. Network issues")
            return
        
        # Load previous products
        previous_products = load_previous_products()
        
        # Find new products
        new_products = find_new_products(current_products, previous_products)
        
        # Send notifications if there are new products
        if new_products:
            send_notification(new_products)
        else:
            print("No new products found")
        
        # Save current products for next run
        save_current_products(current_products)
        
        print(f"Total products tracked: {len(current_products)}")
        
    except TimeoutError:
        print("Script timed out - this may indicate Chrome/Selenium issues")
    except Exception as e:
        print(f"Main function error: {e}")
    finally:
        signal.alarm(0)  # Cancel timeout

if __name__ == "__main__":
    main()
