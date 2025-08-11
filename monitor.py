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
    
    try:
        # Configure Chrome options for GitHub Actions
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--accept-lang=ko-KR,ko,en')
        
        print("Starting Chrome browser...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Wait for products to load - look for common loading indicators
        try:
            # Wait up to 15 seconds for content to appear
            WebDriverWait(driver, 15).until(
                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "a[href*='product'], a[href*='goods'], a[href*='/p/']")) > 0
                or "버터" in driver.page_source
            )
            print("Content loaded successfully")
        except TimeoutException:
            print("Timeout waiting for content to load")
        
        # Additional wait to ensure all dynamic content is loaded
        time.sleep(2)
        
        # Save page source for debugging
        with open('debug_selenium_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("Saved Selenium page HTML to debug_selenium_page.html")
        
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
                
                # Check if element itself is a link
                if element.tag_name == 'a':
                    link_element = element
                else:
                    # Look for link in parent elements
                    parent = element
                    for _ in range(5):  # Check up to 5 levels up
                        parent = parent.find_element(By.XPATH, "..")
                        if parent.tag_name == 'a':
                            link_element = parent
                            break
                        # Or look for a link within the parent
                        links = parent.find_elements(By.TAG_NAME, 'a')
                        if links:
                            link_element = links[0]
                            break
                
                link = ""
                if link_element:
                    link = link_element.get_attribute('href') or ""
                    
                    # Skip if we've already processed this link
                    if link in processed_links:
                        continue
                    processed_links.add(link)
                
                # Clean up title
                title = ' '.join(title.split())[:200]
                
                # Create unique ID
                product_id = hashlib.md5((title + link).encode()).hexdigest()[:8]
                
                product = {
                    'id': product_id,
                    'title': title,
                    'link': link,
                    'found_at': datetime.now().isoformat()
                }
                
                products.append(product)
                print(f"  Found product: {title[:100]}")
                
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
                        
                        title = ' '.join(link_text.split())[:200]
                        product_id = hashlib.md5((title + link_url).encode()).hexdigest()[:8]
                        
                        product = {
                            'id': product_id,
                            'title': title,
                            'link': link_url,
                            'found_at': datetime.now().isoformat()
                        }
                        
                        products.append(product)
                        print(f"  Found product via link: {title[:100]}")
                        
                except Exception as e:
                    continue
        
        driver.quit()
        print(f"Selenium result: Found {len(products)} products with '버터'")
        return products
        
    except WebDriverException as e:
        print(f"Selenium WebDriver error: {e}")
        return []
    except Exception as e:
        print(f"Selenium error: {e}")
        return []

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
    """Main product fetching function"""
    # Try Selenium first (handles JavaScript)
    if SELENIUM_AVAILABLE:
        products = get_products_selenium(url)
        if products:
            return products
    
    # Fall back to requests method
    print("Selenium failed or unavailable, trying requests method...")
    return get_products_requests(url)

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
        message += f"• {title}\n{product['link']}\n\n"
    
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
        print(f"  • {product['title']}")
        print(f"    {product['link']}")
        print()

def main():
    url = "https://thirtymall.com/search?q=%EB%B2%84%ED%84%B0&categoryNo=796224"
    
    print(f"Monitoring: {url}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Selenium available: {SELENIUM_AVAILABLE}")
    
    # Get current products
    current_products = get_products(url)
    
    if not current_products:
        print("No products found - this may be due to:")
        print("1. JavaScript-loaded content (need Selenium)")
        print("2. Bot detection by the website")
        print("3. Site structure changes")
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

if __name__ == "__main__":
    main()
