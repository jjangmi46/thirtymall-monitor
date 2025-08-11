#!/usr/bin/env python3
"""
ThirtyMall Product Monitor - Simplified Working Version
"""

import sys
import requests
import json
import os
import time
from datetime import datetime
import hashlib
import re

print("=== Script Starting ===")
print(f"Python version: {sys.version}")

# Import selenium and webdriver-manager
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    print("✓ All imports successful")
    SELENIUM_AVAILABLE = True
except ImportError as e:
    print(f"✗ Import failed: {e}")
    SELENIUM_AVAILABLE = False
    sys.exit(1)

def get_products(url):
    """Scrape products using Selenium"""
    driver = None
    products = []
    
    try:
        print("\n=== Setting up Chrome ===")
        
        # Chrome options for GitHub Actions
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Install and get ChromeDriver
        print("Installing ChromeDriver...")
        driver_path = ChromeDriverManager().install()
        print(f"ChromeDriver path: {driver_path}")
        
        # Create driver
        print("Starting Chrome...")
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        print("✓ Chrome started successfully")
        
        # Load page
        print(f"\nLoading: {url}")
        driver.get(url)
        print(f"Page title: {driver.title}")
        
        # Wait for page load
        print("Waiting for page to load...")
        time.sleep(5)
        
        # Scroll to load more content
        print("Scrolling page...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Get page source
        page_source = driver.page_source
        print(f"Page loaded, size: {len(page_source)} chars")
        
        # Save debug file
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print("Saved debug_page.html")
        
        # Check for Cloudflare
        if 'cloudflare' in page_source.lower():
            print("⚠️ Cloudflare detected!")
        
        # Search for butter products
        print("\n=== Searching for products ===")
        
        if '버터' not in page_source:
            print("✗ No '버터' found in page")
            return products
        
        print("✓ Found '버터' in page")
        
        # Find all text elements containing 버터
        elements = driver.find_elements(By.XPATH, "//*[contains(text(), '버터')]")
        print(f"Found {len(elements)} elements with '버터'")
        
        processed = set()
        
        for elem in elements[:30]:  # Process up to 30 elements
            try:
                text = elem.text.strip()
                if not text or len(text) < 10 or text in processed:
                    continue
                    
                processed.add(text)
                
                # Extract title (first line with 버터)
                lines = text.split('\n')
                title = ""
                for line in lines:
                    if '버터' in line:
                        title = line.strip()[:200]
                        break
                
                if not title:
                    continue
                
                # Find price
                price = ""
                price_matches = re.findall(r'[\d,]+\s*원', text)
                if price_matches:
                    price = price_matches[0]
                
                # Try to get link
                link = url  # Default to search page
                try:
                    # Look for parent link
                    parent = elem
                    for _ in range(4):
                        parent = parent.find_element(By.XPATH, "..")
                        links = parent.find_elements(By.TAG_NAME, "a")
                        if links:
                            href = links[0].get_attribute("href")
                            if href:
                                link = href
                                break
                except:
                    pass
                
                # Create product
                product_id = hashlib.md5(title.encode()).hexdigest()[:8]
                
                product = {
                    'id': product_id,
                    'title': title,
                    'price': price if price else "Price not found",
                    'link': link,
                    'found_at': datetime.now().isoformat()
                }
                
                products.append(product)
                print(f"✓ Product: {title[:60]}... [{price}]")
                
            except Exception as e:
                continue
        
        # Alternative method: Find by class patterns
        if len(products) < 3:
            print("\nTrying alternative selectors...")
            selectors = [
                "div[class*='product']",
                "div[class*='item']",
                "li[class*='product']",
                "li[class*='item']",
                "article"
            ]
            
            for selector in selectors:
                items = driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    print(f"Checking {len(items)} items with '{selector}'")
                    for item in items[:10]:
                        try:
                            text = item.text
                            if '버터' in text and text not in processed:
                                processed.add(text)
                                lines = text.split('\n')
                                title = next((l for l in lines if '버터' in l), "")[:200]
                                if title:
                                    price = ""
                                    price_match = re.search(r'[\d,]+\s*원', text)
                                    if price_match:
                                        price = price_match.group()
                                    
                                    product_id = hashlib.md5(title.encode()).hexdigest()[:8]
                                    products.append({
                                        'id': product_id,
                                        'title': title,
                                        'price': price if price else "Price not found",
                                        'link': url,
                                        'found_at': datetime.now().isoformat()
                                    })
                                    print(f"✓ Found: {title[:50]}...")
                        except:
                            continue
                
                if len(products) >= 3:
                    break
        
        return products
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return products
        
    finally:
        if driver:
            try:
                driver.quit()
                print("\n✓ Browser closed")
            except:
                pass

def load_previous_products():
    """Load previously saved products"""
    try:
        if os.path.exists('previous_products.json'):
            with open('previous_products.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def save_products(products):
    """Save products to file"""
    try:
        with open('previous_products.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved {len(products)} products")
    except Exception as e:
        print(f"✗ Save failed: {e}")

def send_telegram(new_products):
    """Send Telegram notification"""
    if not new_products:
        return
        
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("✗ Telegram not configured")
        return
    
    message = f"🧈 {len(new_products)} new butter products!\n\n"
    for p in new_products[:5]:
        message += f"• {p['title'][:80]}\n  💰 {p['price']}\n  🔗 {p['link']}\n\n"
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'disable_web_page_preview': True
        })
        if response.status_code == 200:
            print("✓ Telegram sent")
        else:
            print(f"✗ Telegram failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Telegram error: {e}")

def main():
    print("\n" + "="*50)
    print("THIRTYMALL BUTTER MONITOR")
    print("="*50)
    
    url = "https://thirtymall.com/search?q=%EB%B2%84%ED%84%B0&categoryNo=796224"
    
    # Get products
    current = get_products(url)
    
    if not current:
        print("\n⚠️ No products found!")
        print("Check debug_page.html for details")
        return 1
    
    print(f"\n✓ Found {len(current)} total products")
    
    # Check for new products
    previous = load_previous_products()
    previous_ids = {p['id'] for p in previous}
    new_products = [p for p in current if p['id'] not in previous_ids]
    
    if new_products:
        print(f"✓ {len(new_products)} NEW products!")
        send_telegram(new_products)
    else:
        print("No new products")
    
    # Save
    save_products(current)
    
    # Summary
    print("\n=== Summary ===")
    print(f"Total: {len(current)} products")
    print(f"New: {len(new_products)} products")
    if current:
        print("\nSamples:")
        for p in current[:3]:
            print(f"  • {p['title'][:60]}...")
            print(f"    {p['price']}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✗ Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
