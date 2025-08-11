#!/usr/bin/env python3
"""
ThirtyMall Product Monitor - Enhanced Version
Monitors for new products containing '버터' in category 796224
"""

import requests
import json
import os
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
import hashlib

def get_products(url):
    """Scrape products from the search page with better bot detection avoidance"""
    
    # More realistic browser headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    # Add random delay to seem more human-like
    time.sleep(random.uniform(1, 3))
    
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        session.headers.update(headers)
        
        print(f"Requesting: {url}")
        response = session.get(url, timeout=15)
        
        print(f"Response status: {response.status_code}")
        print(f"Response size: {len(response.content)} bytes")
        
        if response.status_code != 200:
            print(f"HTTP Error: {response.status_code}")
            return []
        
        # Save raw HTML for debugging
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("Saved page HTML to debug_page.html")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Debug: Print page title and check if we got the right page
        page_title = soup.find('title')
        print(f"Page title: {page_title.get_text() if page_title else 'No title found'}")
        
        # Look for common Korean e-commerce patterns
        products = []
        
        # More comprehensive selectors for Korean shopping sites
        product_selectors = [
            # Common Korean e-commerce patterns
            '.goods-item', '.product-item', '.item-wrap', '.goods-wrap',
            '.prd-item', '.product-wrap', '.goods-list-item', '.item-box',
            '[class*="goods"]', '[class*="product"]', '[class*="item"]',
            # Generic patterns
            '.list-item', '.search-item', '.result-item',
            # Data attributes
            '[data-product-id]', '[data-goods-id]', '[data-item-id]'
        ]
        
        product_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                product_elements = elements
                break
        
        # If no specific selectors work, try to find links with product-like URLs
        if not product_elements:
            all_links = soup.find_all('a', href=True)
            product_links = [
                link for link in all_links 
                if any(keyword in link.get('href', '').lower() 
                      for keyword in ['product', 'goods', 'item', '/p/', '/g/'])
            ]
            print(f"Found {len(product_links)} product-like links")
            product_elements = product_links
        
        # Last resort: look for any text containing 버터
        if not product_elements:
            butter_elements = soup.find_all(text=lambda text: text and '버터' in text)
            print(f"Found {len(butter_elements)} elements containing '버터'")
            # Get parent elements of text nodes
            product_elements = [elem.parent for elem in butter_elements[:10] if elem.parent]
        
        print(f"Processing {len(product_elements)} potential product elements")
        
        for i, element in enumerate(product_elements[:20]):  # Limit processing
            try:
                # Try multiple approaches to extract product info
                title = ""
                link = ""
                
                # Method 1: Look for title in common places
                title_selectors = [
                    '.goods-name', '.product-name', '.item-name', '.prd-name',
                    '.title', '.name', 'h3', 'h4', 'h5',
                    '[class*="name"]', '[class*="title"]'
                ]
                
                for title_sel in title_selectors:
                    title_elem = element.select_one(title_sel)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        break
                
                # Method 2: If no title found, use element text
                if not title:
                    title = element.get_text(strip=True)[:200]  # Limit length
                
                # Method 3: Look for links
                if element.name == 'a':
                    link = element.get('href', '')
                else:
                    link_elem = element.find('a', href=True)
                    if link_elem:
                        link = link_elem.get('href', '')
                
                # Fix relative URLs
                if link and not link.startswith('http'):
                    if link.startswith('/'):
                        link = 'https://thirtymall.com' + link
                    else:
                        link = 'https://thirtymall.com/' + link
                
                # Skip if no title or title doesn't contain 버터
                if not title or '버터' not in title:
                    continue
                
                # Clean up title
                title = ' '.join(title.split())  # Remove extra whitespace
                
                # Create unique ID
                product_id = hashlib.md5((title + link).encode()).hexdigest()[:8]
                
                product = {
                    'id': product_id,
                    'title': title,
                    'link': link,
                    'found_at': datetime.now().isoformat()
                }
                
                products.append(product)
                print(f"  Product {len(products)}: {title[:100]}")
                
            except Exception as e:
                print(f"Error processing element {i}: {e}")
                continue
        
        print(f"\nFinal result: Found {len(products)} products with '버터'")
        return products
        
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return []
    except Exception as e:
        print(f"Parsing failed: {e}")
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
    
    for product in new_products[:10]:  # Limit to 10 products to avoid message length limits
        title = product['title'][:100]  # Truncate long titles
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
    
    # Send Telegram notification
    send_telegram_notification(new_products)
    
    # Always print to console (visible in GitHub Actions logs)
    print(f"\n🧈 NEW PRODUCTS FOUND ({len(new_products)}):")
    for product in new_products:
        print(f"  • {product['title']}")
        print(f"    {product['link']}")
        print()

def main():
    url = "https://thirtymall.com/search?q=%EB%B2%84%ED%84%B0&categoryNo=796224"
    
    print(f"Monitoring: {url}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Get current products
    current_products = get_products(url)
    
    if not current_products:
        print("No products found - check debug_page.html for the actual page content")
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
