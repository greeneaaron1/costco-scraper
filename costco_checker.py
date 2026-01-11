import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json

class CostcoProductChecker:
    def __init__(self, item_number, direct_url=None):
        self.item_number = item_number
        self.direct_url = direct_url
        self.results_file = 'costco_check_results.json'
        
    def check_costco97(self):
        """Check costco97.com for the product"""
        try:
            urls_to_try = [
                f"https://costco97.com/product/{self.item_number}",
                f"https://costco97.com/item/{self.item_number}",
                f"https://costco97.com/{self.item_number}",
            ]
            
            for url in urls_to_try:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        price_elements = soup.find_all(['span', 'div', 'p'], 
                            class_=lambda x: x and any(word in str(x).lower() 
                            for word in ['price', 'cost', 'dollar']))
                        
                        sale_elements = soup.find_all(text=lambda x: x and any(word in str(x).lower() 
                            for word in ['sale', 'discount', 'clearance', 'save']))
                        
                        import re
                        price_pattern = r'\$\s*(\d+[,\d]*\.?\d*)'
                        prices_found = re.findall(price_pattern, soup.get_text())
                        current_price = prices_found[0].replace(',', '') if prices_found else None
                        
                        if price_elements or 'camp chef' in soup.get_text().lower():
                            return {
                                'available': True,
                                'url': url,
                                'on_sale': len(sale_elements) > 0,
                                'price': current_price,
                                'timestamp': datetime.now().isoformat(),
                                'page_text': soup.get_text()[:500]
                            }
                except:
                    continue
            
            return {
                'available': False,
                'timestamp': datetime.now().isoformat(),
                'message': 'Product not found on costco97.com'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_official_costco(self):
        """Check official Costco.com for the product using Selenium"""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            
            if self.direct_url:
                url = self.direct_url
                print(f"Checking direct URL with browser automation...")
            else:
                url = f"https://www.costco.com/CatalogSearch?keyword={self.item_number}"
                print(f"Searching for item with browser automation...")
            
            # Set up Chrome options for headless browsing
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Initialize the driver
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(url)
                
                # Wait for page to load
                time.sleep(3)
                
                page_source = driver.page_source
                page_text = page_source.lower()
                
                # Check if product is available
                if self.item_number in page_source or self.direct_url:
                    current_price = None
                    
                    # Try to find price using various selectors
                    price_selectors = [
                        '[automation-id="productPriceOutput"]',
                        '.price',
                        '[class*="price"]',
                        '[data-price]',
                        '.your-price'
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_element = driver.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_element.text
                            
                            # Extract price from text
                            import re
                            price_match = re.search(r'\$\s*(\d+[,\d]*\.?\d*)', price_text)
                            if price_match:
                                current_price = price_match.group(1).replace(',', '')
                                break
                        except:
                            continue
                    
                    # If still no price found, try searching in page source
                    if not current_price:
                        import re
                        price_pattern = r'"price[^"]*":\s*"?\$?(\d+\.?\d*)"?'
                        matches = re.findall(price_pattern, page_source)
                        if matches:
                            # Filter out unlikely prices (too low or too high)
                            valid_prices = [p for p in matches if 10 < float(p) < 10000]
                            if valid_prices:
                                current_price = valid_prices[0]
                    
                    # Check for sale indicators
                    sale_words = ['instant savings', 'save', 'sale', 'discount', 'special offer', 'limited time', 'clearance']
                    on_sale = any(word in page_text for word in sale_words)
                    
                    driver.quit()
                    
                    return {
                        'available': True,
                        'url': url,
                        'on_sale': on_sale,
                        'price': current_price,
                        'timestamp': datetime.now().isoformat(),
                        'site': 'costco.com'
                    }
                
                driver.quit()
                
                return {
                    'available': False,
                    'timestamp': datetime.now().isoformat(),
                    'site': 'costco.com'
                }
                
            except Exception as e:
                driver.quit()
                raise e
            
        except ImportError:
            return {
                'error': 'Selenium not installed. Run: pip install selenium',
                'timestamp': datetime.now().isoformat(),
                'site': 'costco.com'
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'site': 'costco.com'
            }
    
    def check_all_sites(self):
        """Check both sites and return results"""
        print(f"Checking for item {self.item_number}...")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print("Checking costco97.com...")
        costco97_result = self.check_costco97()
        
        print("Checking costco.com...")
        official_result = self.check_official_costco()
        
        results = {
            'item_number': self.item_number,
            'check_time': datetime.now().isoformat(),
            'costco97': costco97_result,
            'official_costco': official_result
        }
        
        self.display_results(results)
        
        return results
    
    def display_results(self, results):
        """Display results in a readable format"""
        print("\n" + "-"*60)
        print(f"ITEM #{results['item_number']}")
        print("-"*60)
        
        print("\nCOSTCO97.COM:")
        if results['costco97'].get('available'):
            print("  ✓ PRODUCT FOUND!")
            print(f"  URL: {results['costco97']['url']}")
            if results['costco97'].get('on_sale'):
                print("  🎉 ON SALE!")
            if results['costco97'].get('price'):
                print(f"  Price: ${results['costco97']['price']}")
            else:
                print("  Regular price (no sale indicator found)")
        elif results['costco97'].get('error'):
            print(f"  ✗ Error: {results['costco97']['error']}")
        else:
            print("  ✗ Product not available")
        
        print("\nOFFICIAL COSTCO.COM:")
        if results['official_costco'].get('available'):
            print("  ✓ PRODUCT FOUND!")
            print(f"  URL: {results['official_costco']['url']}")
            if results['official_costco'].get('on_sale'):
                print("  🎉 ON SALE!")
            if results['official_costco'].get('price'):
                print(f"  Price: ${results['official_costco']['price']}")
            else:
                print("  Regular price (no sale indicator found)")
        elif results['official_costco'].get('error'):
            print(f"  ✗ Error: {results['official_costco']['error']}")
        else:
            print("  ✗ Product not available")


class MultiItemChecker:
    def __init__(self, items_config):
        self.items_config = items_config
        self.results_file = 'costco_check_results.txt'
        self.json_file = 'costco_check_history.json'
    
    def check_all_items(self):
        """Check all items and save results"""
        import os
        print("="*60)
        print("COSTCO PRODUCT AVAILABILITY CHECKER")
        print("="*60)
        print(f"Checking {len(self.items_config)} items...")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Working directory: {os.getcwd()}\n")
        
        all_results = []
        
        for item_config in self.items_config:
            item_num = item_config[0]
            direct_url = item_config[1] if len(item_config) > 1 else None
            
            try:
                checker = CostcoProductChecker(item_num, direct_url)
                result = checker.check_all_sites()
                all_results.append(result)
                print()
            except Exception as e:
                print(f"ERROR checking item {item_num}: {e}")
                print()
        
        print("\nAttempting to save results...")
        self.save_results_text(all_results)
        self.save_results_json(all_results)
        
        self.print_summary(all_results)
        
        return all_results
    
    def save_results_text(self, results):
        """Save results in readable text format"""
        import os
        try:
            print(f"  Saving text file to: {os.path.join(os.getcwd(), self.results_file)}")
            
            item_names = {
                "2622193": "Camp Chef 3-burner Propane Stove",
                "1740583": "Unknown Item",
                "100670295": "Unger Car Wash System"
            }
            
            with open(self.results_file, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write("COSTCO PRODUCT CHECK RESULTS\n")
                f.write(f"{datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
                f.write("="*70 + "\n\n")
                
                for result in results:
                    item_num = result['item_number']
                    item_name = item_names.get(item_num, "Unknown Item")
                    
                    f.write(f"ITEM #{item_num} - {item_name}\n")
                    f.write("-"*70 + "\n")
                    
                    # Costco97 results
                    f.write("Costco97.com: ")
                    if result['costco97'].get('available'):
                        f.write("✓ AVAILABLE")
                        if result['costco97'].get('on_sale'):
                            f.write(" - ON SALE!")
                        if result['costco97'].get('price'):
                            f.write(f" - Price: ${result['costco97']['price']}")
                        f.write("\n")
                        f.write(f"  URL: {result['costco97']['url']}\n")
                    else:
                        f.write("Not Available\n")
                    
                    # Costco.com results
                    f.write("Costco.com:   ")
                    if result['official_costco'].get('available'):
                        f.write("✓ AVAILABLE")
                        if result['official_costco'].get('on_sale'):
                            f.write(" - ON SALE!")
                        if result['official_costco'].get('price'):
                            f.write(f" - Price: ${result['official_costco']['price']}")
                        f.write("\n")
                        f.write(f"  URL: {result['official_costco']['url']}\n")
                    else:
                        f.write("Not Available\n")
                    
                    f.write("\n")
                
                f.write("="*70 + "\n")
            
            print(f"  ✓ Text results saved to: {os.path.abspath(self.results_file)}")
            
        except Exception as e:
            print(f"  ✗ ERROR saving text results: {e}")
    
    def save_results_json(self, results):
        """Save results history in JSON format"""
        import os
        try:
            try:
                with open(self.json_file, 'r') as f:
                    history = json.load(f)
            except FileNotFoundError:
                history = []
            except Exception as e:
                history = []
            
            check_entry = {
                'check_time': datetime.now().isoformat(),
                'results': results
            }
            
            history.append(check_entry)
            
            with open(self.json_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            print(f"  ✓ History saved to JSON ({len(history)} total checks)")
                
        except Exception as e:
            print(f"  ✗ ERROR saving JSON history: {e}")
    
    def print_summary(self, results):
        """Print a summary of findings"""
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        items_on_sale = []
        items_available = []
        
        for result in results:
            item_num = result['item_number']
            
            if result['costco97'].get('available') and result['costco97'].get('on_sale'):
                items_on_sale.append((item_num, 'costco97.com'))
            
            if result['official_costco'].get('available') and result['official_costco'].get('on_sale'):
                items_on_sale.append((item_num, 'costco.com'))
            
            if result['costco97'].get('available') or result['official_costco'].get('available'):
                items_available.append(item_num)
        
        if items_on_sale:
            print("\n🎉 ITEMS ON SALE:")
            for item, site in items_on_sale:
                print(f"  • Item #{item} on {site}")
        else:
            print("\n✗ No items currently on sale")
        
        if items_available:
            print("\n✓ ITEMS AVAILABLE:")
            for item in items_available:
                print(f"  • Item #{item}")
        else:
            print("\n✗ No items currently available")
        
        print("\n" + "="*60)


if __name__ == "__main__":
    items_to_check = [
        ("2622193", None),
        ("1740583", None),
        ("100670295", "https://www.costco.com/p/-/unger-professional-rinse-n-go-max-spotless-car-wash-system-bundle/100670295?langId=-1")
    ]
    
    checker = MultiItemChecker(items_to_check)
    checker.check_all_items()
    
    print("\n📝 To run this daily:")
    print("   - Windows: Use Task Scheduler to run this script daily")
    print("   - Mac/Linux: Add to crontab: 0 9 * * * python costco_checker.py")
    print("   - Or use a service like GitHub Actions for cloud scheduling")
    print("\n💡 Results saved to:")
    print(f"   - costco_check_results.txt (readable format)")
    print(f"   - costco_check_history.json (complete history)")
    print("\n⚠️  FIRST TIME SETUP:")
    print("   1. Install Selenium: pip install selenium")
    print("   2. Install Chrome browser (if not already installed)")
    print("   3. Chrome will auto-download the driver on first run")