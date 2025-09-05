#!/usr/bin/env python3
"""
ThirtyMall Product Monitor - Multiple Keywords Version
Monitors for multiple keywords in different categories
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

# ====== CONFIGURATION ======
# Add your search configurations here
SEARCHES = [
    {
        'name': '버터',  # Name for this search (used in notifications)
        'url': 'https://thirtymall.com/search?q=%EB%B2%84%ED%84%B0&categoryNo=796224',
        'keyword': '버터',  # Keyword to look for in products
        'emoji': '🧈'  # Emoji for notifications
    },
    Add more searches here. Examples:
    {
        'name': '생지',
        'url': 'https://thirtymall.com/search?q=%EC%83%9D%EC%A7%80&categoryNo=796235',
        'keyword': '생지',
        'emoji': '🥐'
    },
    # {
    #     'name': '우유',
    #     'url': 'https://thirtymall.com/search?q=%EC%9A%B0%EC%9C%A0&categoryNo=123456',
    #     'keyword': '우유',
    #     'emoji': '🥛'
    # },
]

def setup_driver():
    """Setup Chrome driver once for reuse"""
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
    
    return driver

def get_products(driver, search_config):
    """Scrape products for a specific search"""
    products = []
    url = search_config['url']
    keyword = search_config['keyword']
    search_name = search_config['name']
    
    try:
        print(f"\n=== Searching for {search_name} ===")
        print(f"URL: {url}")
        
        # Load page
        driver.get(url)
        print(f"Page title: {driver.title}")
        
        # Wait for page load
        print("Waiting for page to load...")
        time.sleep(5)
        
        # Scroll to load more content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Get page source
        page_source = driver.page_source
        print(f"Page loaded, size: {len(page_source)} chars")
        
        # Save debug file for this search
        debug_file = f'debug_{search_name}.html'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(page_source[:50000])  # Save first 50k chars
        print(f"Saved {debug_file}")
        
        # Check for keyword
        if keyword not in page_source:
            print(f"✗ No '{keyword}' found in page")
            return products
        
        print(f"✓ Found '{keyword}' in page")
        
        # Find all text elements containing keyword
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
        print(f"Found {len(elements)} elements with '{keyword}'")
        
        processed = set()
        
        for elem in elements[:30]:  # Process up to 30 elements
            try:
                text = elem.text.strip()
                if not text or len(text) < 10 or text in processed:
                    continue
                    
                processed.add(text)
                
                # Extract title (first line with keyword)
                lines = text.split('\n')
                title = ""
                for line in lines:
                    if keyword in line:
                        title = line.strip()[:200]
                        break
                
                if not title:
                    continue
                
                # Find price and discount
                price = ""
                discount = ""
                
                # Find price patterns
                price_matches = re.findall(r'[\d,]+원', text)
                if price_matches:
                    price = price_matches[-1] if len(price_matches) > 1 else price_matches[0]
                
                # Find discount
                discount_matches = re.findall(r'\d+%', text)
                if discount_matches:
                    discount = discount_matches[0]
                
                # Format price
                if discount and price:
                    price = f"{discount} {price}"
                elif not price:
                    price = "가격 정보 없음"
                
                # Try to get link
                link = url
                try:
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
                
                # Create product with search identifier
                product_id = hashlib.md5(f"{search_name}_{title}".encode()).hexdigest()[:8]
                
                product = {
                    'id': product_id,
                    'search_name': search_name,  # Track which search this came from
                    'title': title,
                    'price': price,
                    'link': link,
                    'found_at': datetime.now().isoformat()
                }
                
                products.append(product)
                print(f"✓ Product: {title[:60]}... [{price}]")
                
            except Exception as e:
                continue
        
        # Alternative method: Find by MUI classes
        if len(products) < 3:
            print(f"Trying MUI selectors for {search_name}...")
            items = driver.find_elements(By.CSS_SELECTOR, "div[class*='MuiBox-root']")
            
            for item in items[:20]:
                try:
                    text = item.text
                    if keyword in text and text not in processed:
                        processed.add(text)
                        lines = text.split('\n')
                        title = next((l for l in lines if keyword in l), "")[:200]
                        if title:
                            price = ""
                            discount = ""
                            
                            for line in lines:
                                if '%' in line:
                                    discount = line.strip()
                                elif '원' in line and not price:
                                    price = line.strip()
                            
                            if discount and price:
                                final_price = f"{discount} {price}"
                            elif price:
                                final_price = price
                            else:
                                final_price = "가격 정보 없음"
                            
                            product_id = hashlib.md5(f"{search_name}_{title}".encode()).hexdigest()[:8]
                            products.append({
                                'id': product_id,
                                'search_name': search_name,
                                'title': title,
                                'price': final_price,
                                'link': url,
                                'found_at': datetime.now().isoformat()
                            })
                            print(f"✓ Found: {title[:50]}... [{final_price}]")
                except:
                    continue
        
        print(f"Total {search_name} products found: {len(products)}")
        return products
        
    except Exception as e:
        print(f"✗ Error searching {search_name}: {e}")
        return products

def load_previous_products():
    """Load previously saved products (now supports multiple searches)"""
    try:
        if os.path.exists('previous_products_multi.json'):
            with open('previous_products_multi.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def save_products(products):
    """Save products to file"""
    try:
        with open('previous_products_multi.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved {len(products)} total products")
    except Exception as e:
        print(f"✗ Save failed: {e}")

def send_telegram(new_products_by_search):
    """Send Telegram notification for new products grouped by search"""
    if not any(new_products_by_search.values()):
        return
        
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("✗ Telegram not configured")
        return
    
    # Build message
    message = "🔔 새로운 상품 알림!\n\n"
    
    for search_config in SEARCHES:
        search_name = search_config['name']
        emoji = search_config.get('emoji', '📦')
        
        if search_name in new_products_by_search and new_products_by_search[search_name]:
            products = new_products_by_search[search_name]
            message += f"{emoji} {search_name}: {len(products)}개 신상품\n"
            
            for p in products[:3]:  # Show first 3 products per search
                message += f"  • {p['title'][:60]}\n"
                message += f"    💰 {p['price']}\n"
            
            if len(products) > 3:
                message += f"  ... 외 {len(products)-3}개 더\n"
            
            message += "\n"
    
    # Add link to first product for quick access
    all_new = []
    for products in new_products_by_search.values():
        all_new.extend(products)
    
    if all_new:
        message += f"\n🔗 {all_new[0]['link']}"
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'disable_web_page_preview': False
        })
        if response.status_code == 200:
            print("✓ Telegram sent")
        else:
            print(f"✗ Telegram failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Telegram error: {e}")

def main():
    print("\n" + "="*50)
    print("THIRTYMALL MULTI-KEYWORD MONITOR")
    print("="*50)
    
    print(f"Monitoring {len(SEARCHES)} searches:")
    for search in SEARCHES:
        print(f"  • {search['name']} {search.get('emoji', '')}")
    
    # Setup driver once
    driver = None
    try:
        driver = setup_driver()
        
        # Get products for all searches
        all_current_products = []
        products_by_search = {}
        
        for search_config in SEARCHES:
            products = get_products(driver, search_config)
            all_current_products.extend(products)
            products_by_search[search_config['name']] = products
            time.sleep(3)  # Pause between searches to avoid rate limiting
        
        if not all_current_products:
            print("\n⚠️ No products found in any search!")
            return 1
        
        print(f"\n✓ Found {len(all_current_products)} total products across all searches")
        
        # Check for new products
        previous = load_previous_products()
        previous_ids = {p['id'] for p in previous}
        
        # Group new products by search
        new_products_by_search = {}
        for search_name, products in products_by_search.items():
            new_products = [p for p in products if p['id'] not in previous_ids]
            if new_products:
                new_products_by_search[search_name] = new_products
        
        # Send notifications
        total_new = sum(len(prods) for prods in new_products_by_search.values())
        if total_new > 0:
            print(f"\n✓ {total_new} NEW products found!")
            send_telegram(new_products_by_search)
        else:
            print("\nNo new products in any search")
        
        # Save all products
        save_products(all_current_products)
        
        # Summary
        print("\n=== Summary ===")
        for search_name, products in products_by_search.items():
            new_count = len(new_products_by_search.get(search_name, []))
            print(f"{search_name}: {len(products)} total, {new_count} new")
            if products:
                print(f"  Sample: {products[0]['title'][:50]}... [{products[0]['price']}]")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if driver:
            try:
                driver.quit()
                print("\n✓ Browser closed")
            except:
                pass

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
