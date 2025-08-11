#!/usr/bin/env python3
"""
ThirtyMall Product Monitor - Enhanced Debugging Version
Monitors for new products containing '버터' in category 796224
"""

import sys
import requests
import json
import os
import time
from datetime import datetime
import hashlib
import traceback

print("=== Script Starting ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

# Try to import selenium with webdriver-manager
SELENIUM_AVAILABLE = False
try:
    print("Attempting to import selenium...")
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    print("Selenium imported successfully")
    
    print("Attempting to import webdriver_manager...")
    from webdriver_manager.chrome import ChromeDriverManager
    print("Webdriver-manager imported successfully")
    
    SELENIUM_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    print("Selenium/webdriver-manager not available")
except Exception as e:
    print(f"Unexpected import error: {e}")

def test_network():
    """Test basic network connectivity"""
    print("\n=== Testing Network ===")
    try:
        response = requests.get("https://www.google.com", timeout=5)
        print(f"Google.com status: {response.status_code}")
        
        response = requests.get("https://thirtymall.com", timeout=5)
        print(f"ThirtyMall.com status: {response.status_code}")
        return True
    except Exception as e:
        print(f"Network test failed: {e}")
        return False

def get_products_selenium(url):
    """Scrape products using Selenium with extensive debugging"""
    if not SELENIUM_AVAILABLE:
        print("ERROR: Selenium not available, cannot proceed")
        return []
    
    driver = None
    try:
        print("\n=== Setting up Selenium ===")
        
        # Configure Chrome options
        chrome_options = Options()
        
        # Essential headless options for GitHub Actions
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional options for stability
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Enable logging
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--v=1')
        
        print("Chrome options configured")
        
        # Download and setup ChromeDriver
        print("Installing ChromeDriver via webdriver-manager...")
        try:
            driver_path = ChromeDriverManager().install()
            print(f"ChromeDriver installed at: {driver_path}")
        except Exception as e:
            print(f"ChromeDriver installation failed: {e}")
            print("Trying alternative installation...")
            # Try with specific version
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.core.utils import ChromeType
            driver_path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
            print(f"Chromium driver installed at: {driver_path}")
        
        service = Service(driver_path)
        
        print("Creating Chrome driver instance...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Driver created successfully")
        
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)
        
        print(f"\nLoading URL: {url}")
        driver.get(url)
        print("Page loaded")
        
        # Get page info
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Wait for page to stabilize
        print("Waiting for page to stabilize...")
        time.sleep(5)
        
        # Check page source
        page_source = driver.page_source
        print(f"Page source length: {len(page_source)} characters")
        
        # Save debug info
        debug_file = 'debug_page.html'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"Saved page source to {debug_file}")
        
        # Check if butter is in page
        if '버터' in page_source:
            print("✓ Found '버터' in page source")
        else:
            print("✗ '버터' NOT found in page source")
            print("First 500 chars of page:")
            print(page_source[:500])
        
        # Try scrolling to load more content
        print("\nScrolling page to trigger lazy loading...")
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Search for products
        products = []
        
        print("\n=== Searching for products ===")
        
        # Method 1: XPath search for butter
        butter_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '버터')]")
        print(f"Found {len(butter_elements)} elements containing '버터'")
        
        if len(butter_elements) == 0:
            print("No butter elements found, trying alternative methods...")
            
            # Method 2: Search in all text
            all_elements = driver.find_elements(By.XPATH, "//*")
            butter_count = 0
            for elem in all_elements[:100]:  # Check first 100 elements
                try:
                    if '버터' in elem.text:
                        butter_count += 1
                except:
                    pass
            print(f"Found '버터' in {butter_count} elements via text search")
            
            # Method 3: Check common product selectors
            selectors_to_try = [
                'div[class*="product"]',
                'div[class*="item"]',
                'div[class*="goods"]',
                'li[class*="product"]',
                'li[class*="item"]',
                'article',
                '.product',
                '.item',
                '[data-product]'
            ]
            
            for selector in selectors_to_try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    for elem in elements[:3]:
                        try:
                            text = elem.text[:100]
                            print(f"  Sample text: {text}")
                        except:
                            pass
        
        # Process found elements
        processed_items = set()
        for element in butter_elements[:20]:  # Process max 20 items
            try:
                text = element.text.strip()
                if not text or text in processed_items:
                    continue
                    
                processed_items.add(text)
                
                # Extract title
                lines = text.split('\n')
                title = lines[0] if lines else text[:100]
                
                # Look for price
                import re
                price = ""
                price_patterns = [r'[\d,]+\s*원', r'₩\s*[\d,]+', r'[\d,]+won']
                for pattern in price_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        price = matches[0]
                        break
                
                # Try to get link
                link = url  # Default to search URL
                try:
                    parent = element
                    for _ in range(3):
                        parent = parent.find_element(By.XPATH, "..")
                        links = parent.find_elements(By.TAG_NAME, 'a')
                        if links:
                            link = links[0].get_attribute('href') or url
                            break
                except:
                    pass
                
                product_id = hashlib.md5((title + link).encode()).hexdigest()[:8]
                
                product = {
                    'id': product_id,
                    'title': title[:200],
                    'price': price,
                    'link': link,
                    'found_at': datetime.now().isoformat()
                }
                
                products.append(product)
                print(f"✓ Product found: {title[:60]}... - {price}")
                
            except Exception as e:
                print(f"Error processing element: {e}")
                continue
        
        print(f"\nTotal products found: {len(products)}")
        return products
        
    except Exception as e:
        print(f"\n!!! SELENIUM ERROR !!!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        return []
    finally:
        if driver:
            try:
                print("\nClosing browser...")
                driver.quit()
                print("Browser closed")
            except Exception as e:
                print(f"Error closing browser: {e}")

def load_previous_products():
    """Load previously found products from file"""
    filename = 'previous_products.json'
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                products = json.load(f)
                print(f"Loaded {len(products)} previous products")
                return products
        else:
            print(f"{filename} not found, starting fresh")
            return []
    except Exception as e:
        print(f"Error loading previous products: {e}")
        return []

def save_current_products(products):
    """Save current products to file"""
    filename = 'previous_products.json'
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(products)} products to {filename}")
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
    
    print(f"Sending Telegram notification for {len(new_products)} new products...")
    
    # Prepare message
    message = f"🧈 Found {len(new_products)} new 버터 products!\n\n"
    
    for product in new_products[:10]:
        title = product['title'][:100]
        price = product.get('price', 'No price')
        message += f"• {title}\n  💰 {price}\n  🔗 {product['link']}\n\n"
    
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
            print("✓ Telegram notification sent successfully")
        else:
            print(f"✗ Telegram notification failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Error sending Telegram notification: {e}")

def main():
    print("\n" + "="*50)
    print("THIRTYMALL PRODUCT MONITOR")
    print("="*50)
    
    url = "https://thirtymall.com/search?q=%EB%B2%84%ED%84%B0&categoryNo=796224"
    
    print(f"Target URL: {url}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Running in GitHub Actions: {os.getenv('GITHUB_ACTIONS', 'No')}")
    print(f"Selenium available: {SELENIUM_AVAILABLE}")
    
    # Test network first
    if not test_network():
        print("\n!!! Network test failed, exiting !!!")
        return 1
    
    # Get current products
    print("\n=== Starting product search ===")
    current_products = get_products_selenium(url)
    
    if not current_products:
        print("\n⚠️ WARNING: No products found!")
        print("Possible reasons:")
        print("  1. Site requires Cloudflare bypass")
        print("  2. Products loaded via AJAX after page load")
        print("  3. Site structure changed")
        print("  4. Anti-bot protection detected automation")
        
        # Check debug file
        if os.path.exists('debug_page.html'):
            with open('debug_page.html', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'cloudflare' in content.lower():
                    print("\n!!! Cloudflare detected in page !!!")
                if 'captcha' in content.lower():
                    print("\n!!! CAPTCHA detected in page !!!")
                    
        return 1
    
    # Load previous products
    print("\n=== Checking for new products ===")
    previous_products = load_previous_products()
    
    # Find new products
    new_products = find_new_products(current_products, previous_products)
    
    if new_products:
        print(f"✓ Found {len(new_products)} NEW products!")
        send_telegram_notification(new_products)
    else:
        print("No new products since last check")
    
    # Save current products
    save_current_products(current_products)
    
    print("\n=== Summary ===")
    print(f"Total products tracked: {len(current_products)}")
    print(f"New products: {len(new_products)}")
    
    if current_products:
        print("\nSample products found:")
        for p in current_products[:3]:
            print(f"  • {p['title'][:60]}...")
            print(f"    Price: {p.get('price', 'No price')}")
    
    print("\n=== Script completed successfully ===")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n!!! FATAL ERROR !!!")
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)
