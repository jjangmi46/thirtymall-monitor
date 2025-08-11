#!/usr/bin/env python3
"""
ThirtyMall Product Monitor - Fixed Version with webdriver-manager
Monitors for new products containing '버터' in category 796224
"""

import requests
import json
import os
import time
import random
from datetime import datetime
import hashlib

# Try to import selenium with webdriver-manager
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not available, falling back to requests method")

def get_products_selenium(url):
    """Scrape products using Selenium with automatic driver management"""
    if not SELENIUM_AVAILABLE:
        print("Selenium not installed, cannot handle JavaScript content")
        return []
    
    driver = None
    try:
        print("Setting up Chrome with webdriver-manager...")
        
        # Configure Chrome options
        chrome_options = Options()
        
        # Essential headless options for GitHub Actions
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-images')  # Save bandwidth
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional stability options
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Use webdriver-manager to automatically download and manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        print("Starting Chrome browser...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for initial page load
        time.sleep(3)
        
        # Scroll to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Wait for products to load
        try:
            WebDriverWait(driver, 15).until(
                lambda d: len(d.find_elements(By.XPATH, "//*[contains(text(), '버터')]")) > 0
                or "버터" in d.page_source
            )
            print("Content loaded successfully")
        except TimeoutException:
            print("Timeout waiting for content to load - continuing anyway")
        
        # Additional wait for dynamic content
        time.sleep(2)
        
        # Debug: Save page source
        if os.getenv('GITHUB_ACTIONS'):
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source[:10000])  # First 10k chars for debugging
            print("Saved page HTML for debugging")
        
        # Search for products containing '버터'
        products = []
        processed_items = set()
        
        # Method 1: Find all elements containing '버터'
        butter_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '버터')]")
        print(f"Found {len(butter_elements)} elements containing '버터'")
        
        for element in butter_elements:
            try:
                text = element.text.strip()
                if not text or len(text) < 5:  # Skip very short texts
                    continue
                
                # Try to find the product container
                product_container = element
                for _ in range(5):  # Go up to 5 levels
                    parent = product_container.find_element(By.XPATH, "..")
                    if parent.tag_name in ['li', 'div', 'article', 'section']:
                        # Check if this looks like a product container
                        if len(parent.text) > len(text) and len(parent.text) < 1000:
                            product_container = parent
                            break
                
                # Extract product info
                container_text = product_container.text
                if container_text in processed_items:
                    continue
                processed_items.add(container_text)
                
                # Extract title (first line containing 버터)
                lines = container_text.split('\n')
                title = ""
                for line in lines:
                    if '버터' in line:
                        title = line.strip()
                        break
                
                if not title:
                    continue
                
                # Extract price (look for patterns)
                price = ""
                import re
                price_patterns = [
                    r'[\d,]+\s*원',     # 1,000원
                    r'₩\s*[\d,]+',      # ₩1,000
                    r'KRW\s*[\d,]+',    # KRW 1,000
                    r'[\d,]+won',       # 1,000won
                ]
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, container_text, re.IGNORECASE)
                    if matches:
                        price = matches[0].strip()
                        break
                
                # Try to find link
                link = ""
                try:
                    link_elements = product_container.find_elements(By.TAG_NAME, 'a')
                    if link_elements:
                        link = link_elements[0].get_attribute('href') or ""
                except:
                    pass
                
                # Create product entry
                product_id = hashlib.md5((title + link).encode()).hexdigest()[:8]
                
                product = {
                    'id': product_id,
                    'title': title[:200],
                    'price': price,
                    'link': link if link else url,  # Use search URL if no specific link
                    'found_at': datetime.now().isoformat()
                }
                
                products.append(product)
                print(f"  Found: {title[:80]}... - {price}")
                
            except Exception as e:
                continue
        
        # Method 2: Try finding product cards/containers directly
        if len(products) < 3:  # If we found very few products
            print("Trying alternative selectors...")
            
            # Common Korean e-commerce product selectors
            product_selectors = [
                '.product-item', '.goods-item', '.item-wrap',
                '[class*="product"]', '[class*="goods"]', '[class*="item"]',
                'li[class*="list"]', 'div[class*="box"]'
            ]
            
            for selector in product_selectors:
                try:
                    items = driver.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        print(f"Found {len(items)} items with selector: {selector}")
                        for item in items[:20]:  # Check first 20
                            try:
                                item_text = item.text.strip()
                                if '버터' in item_text and item_text not in processed_items:
                                    processed_items.add(item_text)
                                    
                                    # Extract title
                                    lines = item_text.split('\n')
                                    title = next((line for line in lines if '버터' in line), "")
                                    
                                    if not title:
                                        continue
                                    
                                    # Extract price
                                    price = ""
                                    import re
                                    for pattern in [r'[\d,]+\s*원', r'₩\s*[\d,]+']:
                                        matches = re.findall(pattern, item_text)
                                        if matches:
                                            price = matches[0].strip()
                                            break
                                    
                                    # Get link
                                    link = ""
                                    try:
                                        links = item.find_elements(By.TAG_NAME, 'a')
                                        if links:
                                            link = links[0].get_attribute('href') or ""
                                    except:
                                        pass
                                    
                                    product_id = hashlib.md5((title + link).encode()).hexdigest()[:8]
                                    
                                    product = {
                                        'id': product_id,
                                        'title': title[:200],
                                        'price': price,
                                        'link': link if link else url,
                                        'found_at': datetime.now().isoformat()
                                    }
                                    
                                    products.append(product)
                                    print(f"  Found via selector: {title[:60]}... - {price}")
                                    
                            except Exception as e:
                                continue
                        
                        if len(products) >= 3:
                            break
                            
                except Exception as e:
                    continue
        
        print(f"Total products found: {len(products)}")
        return products
        
    except WebDriverException as e:
        print(f"WebDriver error: {str(e)[:200]}")
        return []
    except Exception as e:
        print(f"Unexpected error: {str(e)[:200]}")
        return []
    finally:
        if driver:
            try:
                driver.quit()
                print("Browser closed")
            except:
                pass
