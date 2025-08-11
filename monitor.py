#!/usr/bin/env python3
"""
ThirtyMall Product Monitor
Monitors for new products containing '버터' in category 796224
"""

import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import hashlib

def get_products(url):
    """Scrape products from the search page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # You'll need to inspect the HTML to find the right selectors
        # These are common patterns - adjust based on actual site structure
        products = []
        
        # Try multiple possible selectors for product containers
        product_selectors = [
            '.product-item', '.item', '.goods-item', '.product',
            '[class*="product"]', '[class*="item"]', '[class*="goods"]'
        ]
        
        product_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                product_elements = elements
                print(f"Found {len(elements)} elements with selector: {selector}")
                break
        
        if not product_elements:
            # Fallback: look for links that might be products
            product_elements = soup.find_all('a', href=True)
            print(f"Fallback: Found {len(product_elements)} links")
        
        for element in product_elements[:20]:  # Limit to first 20 items
            try:
                # Extract product info - adjust selectors based on site structure
                title_element = element.find(['h3', 'h4', 'span', 'div'], class_=lambda x: x and any(word in x.lower() for word in ['title', 'name', 'product']))
                title = title_element.get_text(strip=True) if title_element else element.get_text(strip=True)[:100]
                
                # Skip if title doesn't contain 버터
                if '버터' not in title:
                    continue
                
                # Get product link
                link = element.get('href', '')
                if link and not link.startswith('http'):
                    link = 'https://thirtymall.com' + link
                
                # Create unique ID for the product
                product_id = hashlib.md5((title + link).encode()).hexdigest()[:8]
                
                products.append({
                    'id': product_id,
                    'title': title,
                    'link': link,
                    'found_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"Error processing element: {e}")
                continue
        
        print(f"Found {len(products)} products with '버터'")
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
        print("No products found - might be blocked or site structure changed")
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
