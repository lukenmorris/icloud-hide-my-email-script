"""
iCloud Hide My Email Manager
A tool to automate deactivation and deletion of Hide My Email addresses
"""

import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# Suppress webdriver-manager logs
os.environ['WDM_LOG'] = '0'

# Suppress Selenium logs
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


# Configuration
ICLOUD_URL = "https://www.icloud.com/icloudplus/"
WAIT_TIMEOUT = 20
LOGIN_TIMEOUT = 300

# XPaths for different sections
XPATHS = {
    'active': {
        'header': "/html/body/aside/div/div[1]/div/div/div[2]/section[1]/div/div/div[1]/h2",
        'container': "/html/body/aside/div/div[1]/div/div/div[2]/section[1]/div/div/div[2]/div[2]",
        'search_button': "/html/body/aside/div/div[1]/div/div/div[2]/section[1]/div/div/div[1]/div/div[1]/button",
        'search_input': "/html/body/aside/div/div[1]/div/div/div[2]/section[1]/div/div/div[2]/div[1]/div/input"
    },
    'inactive': {
        'header': "/html/body/aside/div/div[1]/div/div/div[2]/section[3]/div/div[1]/h2",
        'container': "/html/body/aside/div/div[1]/div/div/div[2]/section[3]/div",
        'search_button': "/html/body/aside/div/div[1]/div/div/div[2]/section[3]/div/div[1]/div/div/button",
        'search_input': "/html/body/aside/div/div[1]/div/div/div[2]/section[3]/div/div[2]/div[1]/div/input"
    }
}


class EmailManager:
    """Manages the deactivation and deletion of Hide My Email addresses"""
    
    def __init__(self):
        self.driver = None
        self.search_term = None
        self.mode = None
        self.original_mode = None
        self.deactivated_count = 0
        self.deleted_count = 0
        self.headless_mode = False
        self.operation_start_time = None
        self.is_purge_mode = False
        
    def estimate_time_remaining(self, processed, total, start_time):
        """Estimate time remaining based on current pace"""
        if processed == 0:
            return "Calculating..."
        
        elapsed = time.time() - start_time
        if elapsed < 1:  # Avoid division issues
            return "Calculating..."
            
        rate = processed / elapsed  # emails per second
        remaining = total - processed
        eta_seconds = remaining / rate if rate > 0 else 0
        
        if eta_seconds < 60:
            return f"{eta_seconds:.0f} seconds"
        elif eta_seconds < 3600:
            return f"{eta_seconds/60:.1f} minutes"
        else:
            return f"{eta_seconds/3600:.1f} hours"
    
    def format_elapsed_time(self, start_time):
        """Format elapsed time in human-readable format"""
        elapsed = time.time() - start_time
        if elapsed < 60:
            return f"{elapsed:.0f} seconds"
        elif elapsed < 3600:
            return f"{elapsed/60:.1f} minutes"
        else:
            return f"{elapsed/3600:.1f} hours"
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with options"""
        print("Configuring Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--silent")
        
        print("Setting up Chrome driver...")
        service = ChromeService(ChromeDriverManager().install())
        service.log_path = os.devnull  # Suppress driver logs
        
        self.driver = webdriver.Chrome(
            service=service,
            options=chrome_options
        )
        
    def login_to_icloud(self):
        """Navigate to iCloud and handle login process"""
        print(f"Navigating to {ICLOUD_URL}...")
        self.driver.get(ICLOUD_URL)
        
        # Click initial sign in button
        print("Looking for the initial 'Sign In' button...")
        initial_sign_in_button = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "sign-in-button"))
        )
        initial_sign_in_button.click()
        print("Clicked initial 'Sign In' button.")
        
        # Wait for manual login
        print("\n" + "="*50)
        print(">>> ACTION REQUIRED <<<")
        print("Please complete the login process in the browser window.")
        print("The script will automatically continue once you land on the iCloud+ Features page.")
        print("="*50 + "\n")
        
        WebDriverWait(self.driver, LOGIN_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "icloud-plus-page-route"))
        )
        print("✅ Login successful! iCloud+ Features page detected.")
        
        # Ask about headless mode after successful login
        self.prompt_headless_mode()
        
    def prompt_headless_mode(self):
        """Ask user if they want to switch to headless mode after login"""
        print("\n" + "="*50)
        print("HEADLESS MODE OPTION")
        print("="*50)
        print("Headless mode runs the browser in the background (no visible window).")
        print("This can be less distracting and may run slightly faster.")
        print("Note: You won't be able to see what's happening.")
        print("="*50)
        
        use_headless = self.get_user_input(
            "Would you like to switch to headless mode? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        )
        
        if use_headless in ['yes', 'y']:
            print("Switching to headless mode...")
            self.switch_to_headless()
        else:
            print("Continuing with visible browser window...")
            
    def switch_to_headless(self):
        """Switch from regular to headless mode by recreating the driver"""
        try:
            # Save the current page URL and cookies
            current_url = self.driver.current_url
            cookies = self.driver.get_cookies()
            
            # Close the current driver
            self.driver.quit()
            
            # Create new headless driver
            print("Setting up headless Chrome driver...")
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")  # Use new headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--silent")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Suppress all console output in headless mode
            if os.name == 'nt':  # Windows
                chrome_options.add_argument("--disable-console")
            
            service = ChromeService(ChromeDriverManager().install())
            service.log_path = os.devnull  # Suppress driver logs
            service.creation_flags = 0x08000000 if os.name == 'nt' else 0  # CREATE_NO_WINDOW on Windows
            
            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            
            # Navigate back to the page
            self.driver.get(current_url)
            
            # Restore cookies to maintain session
            for cookie in cookies:
                # Remove 'sameSite' if it causes issues
                if 'sameSite' in cookie:
                    del cookie['sameSite']
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass  # Some cookies might not be addable, that's okay
                    
            # Refresh to apply cookies
            self.driver.refresh()
            
            # Wait for page to load and verify we're still logged in
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "icloud-plus-page-route"))
            )
            
            print("✅ Successfully switched to headless mode!")
            self.headless_mode = True
            
        except Exception as e:
            print(f"⚠️ Failed to switch to headless mode: {e}")
            print("Falling back to visible mode...")
            # If switching fails, recreate the visible driver
            self.setup_driver()
            self.driver.get(current_url)
            for cookie in cookies:
                if 'sameSite' in cookie:
                    del cookie['sameSite']
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
            self.driver.refresh()
    
    def open_hide_my_email(self):
        """Open the Hide My Email modal"""
        print("Looking for the 'Hide My Email' tile...")
        hide_my_email_tile = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//article[@aria-label='Hide My Email']"))
        )
        hide_my_email_tile.click()
        print("Successfully clicked the 'Hide My Email' tile.")
        
        print("Waiting for the 'Hide My Email' modal to appear...")
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@data-name='hidemyemail']"))
        )
        print("Successfully switched to the 'Hide My Email' modal.")
        
    def get_user_input(self, prompt, valid_options):
        """Get validated user input"""
        while True:
            response = input(prompt).lower()
            if response in valid_options:
                return response
            print(f"Invalid input. Please enter one of: {', '.join(valid_options)}")
            
    def select_mode(self):
        """Get operation mode from user"""
        mode = self.get_user_input(
            "Select a mode:\n"
            "1. Deactivate active emails\n"
            "2. Permanently delete inactive emails\n"
            "3. Purge mode (deactivate then delete)\n"
            "4. Preview mode (view emails without changes)\n"
            "5. Exit\n"
            "Enter choice (1, 2, 3, 4, or 5): ",
            ['1', '2', '3', '4', '5']
        )
        
        if mode == '5':
            print("Exiting... Thank you for using Hide My Email Manager!")
            print("You can close the browser window manually.")
            exit()
            
        self.mode = mode
        self.original_mode = mode
        
        if mode == '3':
            self.handle_purge_confirmation()
        elif mode == '4':
            self.preview_mode()
            
    def preview_mode(self):
        """Preview emails without making any changes"""
        print("\n" + "="*60)
        print("📋 PREVIEW MODE")
        print("="*60)
        print("This mode shows emails without making any changes.")
        print("="*60 + "\n")
        
        # Ask which section to preview
        section_choice = self.get_user_input(
            "Which emails would you like to preview?\n"
            "1. Active emails\n"
            "2. Inactive emails\n"
            "3. Both\n"
            "Enter choice (1, 2, or 3): ",
            ['1', '2', '3']
        )
        
        # Ask about search filter
        use_search = self.get_user_input(
            "Do you want to filter by a search term? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        )
        
        search_term = None
        if use_search in ['yes', 'y']:
            search_term = input("Enter search term: ").strip()
            
        # Preview active emails
        if section_choice in ['1', '3']:
            self.preview_section('active', search_term)
            
        # Preview inactive emails  
        if section_choice in ['2', '3']:
            self.preview_section('inactive', search_term)
            
        print("\n" + "="*60)
        print("Preview complete. No changes were made.")
        print("="*60)
        
        # Return to prevent further processing
        self.mode = None
        
    def preview_section(self, section, search_term=None):
        """Preview emails in a specific section"""
        print(f"\n{'='*50}")
        print(f"📧 {section.upper()} EMAILS")
        print(f"{'='*50}")
        
        # Apply search if needed
        if search_term:
            print(f"Applying filter: '{search_term}'...")
            self.apply_search_filter(section)
            search_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, XPATHS[section]['search_input']))
            )
            search_input.clear()
            search_input.send_keys(search_term)
            time.sleep(3)
        
        # Get email count and items
        total, relevant, items = self.get_email_count(section)
        
        if search_term:
            print(f"\nFound {relevant} {section} emails matching '{search_term}' (Total {section}: {total})")
        else:
            print(f"\nTotal {section} emails: {relevant}")
            
        if relevant == 0:
            print(f"No {section} emails found.")
            return
            
        # Ask how many to display
        if relevant > 20:
            display_choice = self.get_user_input(
                f"\nFound {relevant} emails. How many would you like to see?\n"
                "1. First 20\n"
                "2. First 50\n"
                "3. All\n"
                "Enter choice (1, 2, or 3): ",
                ['1', '2', '3']
            )
            
            display_count = {
                '1': 20,
                '2': 50,
                '3': relevant
            }[display_choice]
        else:
            display_count = relevant
            
        print(f"\nDisplaying {min(display_count, relevant)} {section} emails:")
        print("-" * 50)
        
        # Display emails
        displayed = 0
        for i, item in enumerate(items[:display_count], 1):
            try:
                email_address = item.find_element(By.CLASS_NAME, "searchable-card-subtitle").text
                print(f"{i:3}. {email_address}")
                displayed += 1
                
                # Add a small delay every 10 items to avoid overwhelming
                if i % 10 == 0:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"{i:3}. [Error reading email: {e}]")
                
        print("-" * 50)
        print(f"Displayed {displayed} of {relevant} {section} emails")
        
        # Show summary by service if more than 10 emails
        if displayed >= 10:
            self.show_email_summary(items[:display_count])
            
    def show_email_summary(self, items):
        """Show summary of emails by service/domain"""
        services = {}
        
        for item in items:
            try:
                email = item.find_element(By.CLASS_NAME, "searchable-card-subtitle").text
                # Extract service name (part before @ and after last .)
                if '@' in email:
                    prefix = email.split('@')[0]
                    # Get the last part before dots (usually the service name)
                    parts = prefix.split('.')
                    service = parts[-1] if parts else prefix
                    services[service] = services.get(service, 0) + 1
            except:
                continue
                
        if services:
            print("\n📊 Summary by service:")
            sorted_services = sorted(services.items(), key=lambda x: x[1], reverse=True)
            for service, count in sorted_services[:10]:  # Show top 10
                print(f"   • {service}: {count} email{'s' if count > 1 else ''}")
    
    def preview_and_confirm_operation(self, section, action, search_term=None):
        """Preview emails that will be affected and get confirmation"""
        print(f"\n{'='*60}")
        print(f"⚠️  OPERATION PREVIEW")
        print(f"{'='*60}")
        
        action_text = {
            'deactivate': 'DEACTIVATED',
            'delete': 'PERMANENTLY DELETED',
            'purge': 'PURGED (deactivated then deleted)'
        }[action]
        
        print(f"The following emails will be {action_text}:")
        print(f"{'='*60}\n")
        
        # Get emails that will be affected
        total, relevant, items = self.get_email_count(section)
        
        if relevant == 0:
            print(f"No {section} emails found{f' matching {search_term}' if search_term else ''}.")
            return False
            
        # Collect email addresses
        emails_to_process = []
        for item in items:
            try:
                email_address = item.find_element(By.CLASS_NAME, "searchable-card-subtitle").text
                emails_to_process.append(email_address)
            except:
                continue
                
        # Display emails that will be affected
        display_limit = 50  # Show first 50 in detail
        print(f"📋 Emails to be {action_text.lower()}: {len(emails_to_process)} total")
        
        if search_term:
            print(f"🔍 Filter applied: '{search_term}'")
        
        print("\n" + "-"*50)
        
        # Show the emails
        for i, email in enumerate(emails_to_process[:display_limit], 1):
            print(f"{i:3}. {email}")
            
        if len(emails_to_process) > display_limit:
            print(f"\n... and {len(emails_to_process) - display_limit} more emails")
            
        print("-"*50)
        
        # Show summary by service
        if len(emails_to_process) >= 5:
            services = {}
            for email in emails_to_process:
                if '@' in email:
                    prefix = email.split('@')[0]
                    parts = prefix.split('.')
                    service = parts[-1] if parts else prefix
                    services[service] = services.get(service, 0) + 1
                    
            if services:
                print("\n📊 Summary by service:")
                sorted_services = sorted(services.items(), key=lambda x: x[1], reverse=True)
                for service, count in sorted_services[:10]:
                    print(f"   • {service}: {count} email{'s' if count > 1 else ''}")
        
        # Final confirmation
        print(f"\n{'='*60}")
        print(f"⚠️  FINAL CONFIRMATION REQUIRED ⚠️")
        print(f"{'='*60}")
        print(f"You are about to {action} {len(emails_to_process)} email{'s' if len(emails_to_process) > 1 else ''}.")
        
        if action in ['delete', 'purge']:
            print("❗ This action is PERMANENT and cannot be undone!")
            
        print(f"{'='*60}\n")
        
        # Extra confirmation for large operations
        if len(emails_to_process) > 20:
            print(f"⚠️  WARNING: This is a large operation ({len(emails_to_process)} emails)")
            print("It may take several minutes to complete.\n")
            
        confirm = self.get_user_input(
            f"Do you want to proceed with {action} operation? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        )
        
        if confirm in ['yes', 'y']:
            estimated_time = len(emails_to_process) * 3  # Roughly 3 seconds per email
            if estimated_time > 60:
                print(f"\n⏱️  Estimated time: {estimated_time/60:.1f} minutes")
            print(f"\n✅ Confirmed. Starting {action} operation...")
            print("="*60 + "\n")
            return True
        else:
            print(f"\n❌ Operation cancelled. No emails were {action_text.lower()}.")
            return False
                
    def handle_purge_confirmation(self):
        """Handle confirmation for purge mode"""
        print("\n" + "="*60)
        print("⚠️  PURGE MODE WARNING ⚠️")
        print("="*60)
        print("Purge mode will:")
        print("1. Deactivate active emails")
        print("2. Then permanently DELETE those emails")
        print("This action cannot be undone!")
        print("="*60)
        
        confirm = self.get_user_input(
            "Are you sure you want to proceed with PURGE mode? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        )
        
        if confirm in ['no', 'n']:
            print("Purge mode cancelled. Exiting script.")
            print("You can close the browser window manually.")
            exit()
            
        print("Purge mode confirmed. Proceeding...")
        
        # Ask about search filter for purge mode
        use_search = self.get_user_input(
            "Do you want to filter by a specific search term? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        )
        
        if use_search in ['yes', 'y']:
            self.search_term = self.get_search_term()
        else:
            self.confirm_purge_all()
            
    def confirm_purge_all(self):
        """Extra confirmation for purging all emails"""
        print("\n" + "="*60)
        print("⚠️⚠️⚠️  EXTREME WARNING ⚠️⚠️⚠️")
        print("="*60)
        print("You are about to purge ALL emails!")
        print("This will:")
        print("1. Deactivate ALL active Hide My Email addresses")
        print("2. Permanently DELETE ALL Hide My Email addresses")
        print("This is IRREVERSIBLE!")
        print("="*60)
        
        final_confirm = self.get_user_input(
            "Are you ABSOLUTELY SURE you want to purge ALL emails? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        )
        
        if final_confirm in ['no', 'n']:
            print("Purge all cancelled. Exiting script.")
            print("You can close the browser window manually.")
            exit()
            
        print("Purging ALL emails confirmed. Proceeding...")
        
    def get_search_term(self):
        """Get search term from user"""
        while True:
            term = input("Enter the search term for emails to filter/purge: ").strip()
            if term:
                print(f"Will filter for emails containing '{term}'...")
                return term
            print("Search term cannot be empty.")
            
    def setup_search_filter(self):
        """Setup search filtering if needed"""
        if self.mode != '3':  # Not purge mode
            use_search = self.get_user_input(
                "Do you want to filter by a specific search term? (yes/no): ",
                ['yes', 'y', 'no', 'n']
            )
            
            if use_search in ['yes', 'y']:
                self.search_term = self.get_search_term()
                
        if self.search_term:
            self.apply_search_filter('active' if self.mode in ['1', '3'] else 'inactive')
        else:
            print("No search filter applied - processing all emails...")
            time.sleep(2)
            
    def apply_search_filter(self, section):
        """Apply search filter to specified section"""
        print(f"Applying search filter to {section} section...")
        search_button = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, XPATHS[section]['search_button']))
        )
        search_button.click()
        
        search_input = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, XPATHS[section]['search_input']))
        )
        search_input.clear()
        search_input.send_keys(self.search_term)
        time.sleep(3)
        
    def get_email_count(self, section):
        """Get count of emails in the specified section"""
        try:
            header = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, XPATHS[section]['header']))
            )
            total_count = header.text.split()[0]
            
            # Try to get container and count items
            try:
                container = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, XPATHS[section]['container']))
                )
                items = container.find_elements(By.XPATH, ".//li[contains(@class, 'card-list-item-platter')]")
                relevant_count = len(items)
            except TimeoutException:
                # Fallback method
                print(f"Using fallback method to find {section} emails...")
                section_num = '1' if section == 'active' else '3'
                items = self.driver.find_elements(
                    By.XPATH, f"//section[{section_num}]//li[contains(@class, 'card-list-item-platter')]"
                )
                relevant_count = len(items)
                
            return total_count, relevant_count, items
            
        except Exception as e:
            print(f"Error getting {section} email count: {e}")
            return "0", 0, []
            
    def process_email_item(self, item, action):
        """Process a single email item (deactivate or delete)"""
        try:
            # Get email address
            email_address = item.find_element(By.CLASS_NAME, "searchable-card-subtitle").text
            print(f"Processing: {email_address}")
            
            # Expand item
            expand_button = item.find_element(By.CLASS_NAME, "button-expand")
            self.driver.execute_script("arguments[0].click();", expand_button)
            time.sleep(2)
            
            # Perform action
            if action == 'deactivate':
                button_text = 'Deactivate email address'
                confirm_text = 'Deactivate'
            else:  # delete
                button_text = 'Delete address'
                confirm_text = 'Delete'
                
            action_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[text()='{button_text}']"))
            )
            self.driver.execute_script("arguments[0].click();", action_button)
            
            time.sleep(1)
            confirm_xpath = f"//button[.//span[text()='{confirm_text}']]"
            confirm_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, confirm_xpath))
            )
            print(f"--> {action.capitalize()[:-1]}ing {email_address}...")
            self.driver.execute_script("arguments[0].click();", confirm_button)
            
            WebDriverWait(self.driver, 15).until(
                EC.invisibility_of_element_located((By.XPATH, confirm_xpath))
            )
            
            return True, email_address  # Return success and email address
            
        except TimeoutException:
            print(f"Error: No '{button_text}' button found. Stopping.")
            return False, None
        except Exception as e:
            print(f"Error processing email: {e}")
            return False, None
    
    def estimate_time_remaining(self, processed, total, start_time):
        """Estimate time remaining based on current pace"""
        if processed == 0:
            return "Calculating..."
        
        elapsed = time.time() - start_time
        if elapsed < 1:  # Avoid division issues
            return "Calculating..."
            
        rate = processed / elapsed  # emails per second
        remaining = total - processed
        eta_seconds = remaining / rate if rate > 0 else 0
        
        if eta_seconds < 60:
            return f"{eta_seconds:.0f} seconds"
        elif eta_seconds < 3600:
            return f"{eta_seconds/60:.1f} minutes"
        else:
            return f"{eta_seconds/3600:.1f} hours"
    
    def format_elapsed_time(self, start_time):
        """Format elapsed time in human-readable format"""
        elapsed = time.time() - start_time
        if elapsed < 60:
            return f"{elapsed:.0f} seconds"
        elif elapsed < 3600:
            return f"{elapsed/60:.1f} minutes"
        else:
            return f"{elapsed/3600:.1f} hours"
    
    def preview_purge_operation(self):
        """Preview both active and inactive emails for purge operation"""
        print(f"\n{'='*60}")
        print(f"⚠️  PURGE OPERATION PREVIEW")
        print(f"{'='*60}")
        print("The following emails will be PURGED (deactivated then deleted):")
        print(f"{'='*60}\n")
        
        # Get active emails
        if self.search_term:
            self.apply_search_filter('active')
            search_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, XPATHS['active']['search_input']))
            )
            search_input.clear()
            search_input.send_keys(self.search_term)
            time.sleep(3)
            
        active_total, active_relevant, active_items = self.get_email_count('active')
        
        active_emails = []
        for item in active_items:
            try:
                email_address = item.find_element(By.CLASS_NAME, "searchable-card-subtitle").text
                active_emails.append(email_address)
            except:
                continue
                
        # Get inactive emails (in case some are already inactive)
        if self.search_term:
            self.apply_search_filter('inactive')
            search_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, XPATHS['inactive']['search_input']))
            )
            search_input.clear()
            search_input.send_keys(self.search_term)
            time.sleep(3)
            
        inactive_total, inactive_relevant, inactive_items = self.get_email_count('inactive')
        
        inactive_emails = []
        for item in inactive_items:
            try:
                email_address = item.find_element(By.CLASS_NAME, "searchable-card-subtitle").text
                inactive_emails.append(email_address)
            except:
                continue
                
        total_affected = len(active_emails) + len(inactive_emails)
        
        if total_affected == 0:
            print(f"No emails found{f' matching {self.search_term}' if self.search_term else ''}.")
            return False
            
        # Display summary
        print(f"📋 Total emails to be purged: {total_affected}")
        if self.search_term:
            print(f"🔍 Filter applied: '{self.search_term}'")
        print(f"\n   • Active emails to deactivate: {len(active_emails)}")
        print(f"   • Inactive emails to delete: {len(inactive_emails)}")
        
        print("\n" + "-"*50)
        
        # Show active emails
        if active_emails:
            print("\n🟢 ACTIVE emails (will be deactivated first):")
            for i, email in enumerate(active_emails[:25], 1):
                print(f"   {i:3}. {email}")
            if len(active_emails) > 25:
                print(f"   ... and {len(active_emails) - 25} more active emails")
                
        # Show inactive emails
        if inactive_emails:
            print("\n🔴 INACTIVE emails (will be permanently deleted):")
            for i, email in enumerate(inactive_emails[:25], 1):
                print(f"   {i:3}. {email}")
            if len(inactive_emails) > 25:
                print(f"   ... and {len(inactive_emails) - 25} more inactive emails")
                
        print("-"*50)
        
        # Final confirmation
        print(f"\n{'='*60}")
        print(f"⚠️⚠️  FINAL PURGE CONFIRMATION  ⚠️⚠️")
        print(f"{'='*60}")
        print(f"You are about to PERMANENTLY PURGE {total_affected} email{'s' if total_affected > 1 else ''}:")
        print(f"   • {len(active_emails)} will be deactivated")
        print(f"   • {len(active_emails) + len(inactive_emails)} will be permanently deleted")
        print("\n❗❗ This action is IRREVERSIBLE! ❗❗")
        print(f"{'='*60}\n")
        
        if total_affected > 20:
            estimated_time = total_affected * 3  # Roughly 3 seconds per email
            print(f"⚠️  WARNING: Large operation ({total_affected} emails)")
            print(f"⏱️  Estimated time: {estimated_time/60:.1f} minutes\n")
            
        confirm = self.get_user_input(
            f"Are you ABSOLUTELY SURE you want to PURGE {total_affected} emails? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        )
        
        if confirm in ['yes', 'y']:
            print(f"\n✅ Purge confirmed. Starting operation...")
            print("="*60 + "\n")
            return True
        else:
            print(f"\n❌ Purge cancelled. No emails were affected.")
            return False
            
    def deactivate_emails(self):
        """Deactivate active emails"""
        # For purge mode, use special preview
        if self.is_purge_mode:
            if not self.preview_purge_operation():
                self.deactivated_count = 0
                return
        else:
            # Regular deactivation preview
            if not self.preview_and_confirm_operation('active', 'deactivate', self.search_term):
                self.deactivated_count = 0
                return
            
        mode_indicator = " (HEADLESS MODE)" if self.headless_mode else ""
        print(f"Starting Deactivation process{mode_indicator}...")
        processed_count = 0
        self.operation_start_time = time.time()
        initial_total = None
        
        while True:
            try:
                total, relevant, items = self.get_email_count('active')
                
                # Store initial total for progress tracking
                if initial_total is None:
                    initial_total = relevant
                
                # Display count with progress
                if self.search_term:
                    print(f"\nRemaining active emails matching '{self.search_term}': {relevant} (Total active: {total})")
                else:
                    print(f"\nRemaining active emails: {relevant}")
                
                # Show progress and time estimate if we've processed some
                if processed_count > 0 and initial_total > 0:
                    progress_pct = (processed_count / initial_total) * 100
                    elapsed = self.format_elapsed_time(self.operation_start_time)
                    eta = self.estimate_time_remaining(processed_count, initial_total, self.operation_start_time)
                    print(f"Progress: {processed_count}/{initial_total} ({progress_pct:.1f}%) | Elapsed: {elapsed} | ETA: {eta}")
                    
                # Check if done
                if total in ["0", "no"] or relevant == 0:
                    if self.search_term and relevant == 0:
                        print(f"No active emails found matching '{self.search_term}'.")
                    else:
                        print("No active emails remaining.")
                    break
                    
                if not items:
                    print("No more active emails found to process.")
                    break
                    
                # Process first item
                success, email_address = self.process_email_item(items[0], 'deactivate')
                if success:
                    processed_count += 1
                    print(f"✅ Successfully deactivated email #{processed_count}: {email_address}")
                    
                    # Show rate after every 5 emails
                    if processed_count % 5 == 0:
                        elapsed = time.time() - self.operation_start_time
                        rate = processed_count / elapsed if elapsed > 0 else 0
                        print(f"   📊 Rate: {rate:.1f} emails/minute")
                    
                    time.sleep(2)
                    
                    # Reapply search if needed
                    if self.search_term:
                        self.apply_search_filter('active')
                else:
                    break
                    
            except (TimeoutException, IndexError):
                print("No more active email addresses found.")
                break
            except StaleElementReferenceException:
                print("Page structure changed. Re-searching for elements...")
                continue
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Stopping to prevent processing wrong emails.")
                break
        
        # Final summary
        if processed_count > 0:
            total_time = self.format_elapsed_time(self.operation_start_time)
            print(f"\n✅ Deactivation complete!")
            print(f"   • Total deactivated: {processed_count}")
            print(f"   • Time taken: {total_time}")
            if self.operation_start_time:
                elapsed = time.time() - self.operation_start_time
                if elapsed > 0:
                    rate = (processed_count / elapsed) * 60
                    print(f"   • Average rate: {rate:.1f} emails/minute")
        else:
            print(f"\n✅ Deactivation complete. No emails were deactivated.")
            
        self.deactivated_count = processed_count
        
    def delete_emails(self):
        """Delete inactive emails"""
        # Skip preview if we're in purge mode (already shown combined preview)
        if not self.is_purge_mode:
            # Regular deletion preview
            if not self.preview_and_confirm_operation('inactive', 'delete', self.search_term):
                self.deleted_count = 0
                return
            
        mode_indicator = " (HEADLESS MODE)" if self.headless_mode else ""
        print(f"Starting Deletion process{mode_indicator}...")
        processed_count = 0
        self.operation_start_time = time.time()
        initial_total = None
        
        while True:
            try:
                total, relevant, items = self.get_email_count('inactive')
                
                # Store initial total for progress tracking
                if initial_total is None:
                    initial_total = relevant
                
                # Display count with progress
                if self.search_term:
                    print(f"\nRemaining inactive emails matching '{self.search_term}': {relevant} (Total inactive: {total})")
                else:
                    print(f"\nRemaining inactive emails: {relevant}")
                
                # Show progress and time estimate if we've processed some
                if processed_count > 0 and initial_total > 0:
                    progress_pct = (processed_count / initial_total) * 100
                    elapsed = self.format_elapsed_time(self.operation_start_time)
                    eta = self.estimate_time_remaining(processed_count, initial_total, self.operation_start_time)
                    print(f"Progress: {processed_count}/{initial_total} ({progress_pct:.1f}%) | Elapsed: {elapsed} | ETA: {eta}")
                    
                # Check if done
                if total in ["0", "no"] or relevant == 0:
                    if self.search_term and relevant == 0:
                        print(f"No inactive emails found matching '{self.search_term}'.")
                    else:
                        print("No inactive emails remaining.")
                    break
                    
                if not items:
                    print("No more inactive emails found to process.")
                    break
                    
                # Process first item
                success, email_address = self.process_email_item(items[0], 'delete')
                if success:
                    processed_count += 1
                    print(f"✅ Successfully deleted email #{processed_count}: {email_address}")
                    
                    # Show rate after every 5 emails
                    if processed_count % 5 == 0:
                        elapsed = time.time() - self.operation_start_time
                        rate = processed_count / elapsed if elapsed > 0 else 0
                        print(f"   📊 Rate: {rate:.1f} emails/minute")
                    
                    time.sleep(2)
                    
                    # Reapply search if needed
                    if self.search_term:
                        self.apply_search_filter('inactive')
                else:
                    break
                    
            except (TimeoutException, IndexError):
                print("No more inactive email addresses found.")
                break
            except StaleElementReferenceException:
                print("Page structure changed. Re-searching for elements...")
                continue
            except Exception as e:
                print(f"An error occurred: {e}")
                break
        
        # Final summary
        if processed_count > 0:
            total_time = self.format_elapsed_time(self.operation_start_time)
            print(f"\n✅ Deletion complete!")
            print(f"   • Total deleted: {processed_count}")
            print(f"   • Time taken: {total_time}")
            if self.operation_start_time:
                elapsed = time.time() - self.operation_start_time
                if elapsed > 0:
                    rate = (processed_count / elapsed) * 60
                    print(f"   • Average rate: {rate:.1f} emails/minute")
        else:
            print(f"\n✅ Deletion complete. No emails were deleted.")
            
        self.deleted_count = processed_count
        
    def run_purge_transition(self):
        """Transition from deactivation to deletion in purge mode"""
        print("\n" + "="*50)
        print("Proceeding to deletion phase of purge...")
        if self.deactivated_count == 0:
            print("No active emails were found, but checking for inactive emails...")
        print("="*50 + "\n")
        time.sleep(3)  # Reduced from original sleep time
        
        if self.search_term:
            self.apply_search_filter('inactive')
        else:
            print("Proceeding to delete ALL inactive emails...")
            
        self.mode = '2'  # Switch to deletion mode
        
    def show_purge_summary(self):
        """Show summary for purge mode"""
        print("\n" + "="*50)
        print("🗑️  PURGE COMPLETE!")
        print(f"Emails deactivated: {self.deactivated_count}")
        print(f"Emails deleted: {self.deleted_count}")
        
        if self.search_term:
            print(f"Total emails purged for '{self.search_term}': {self.deleted_count}")
            if self.deactivated_count == 0 and self.deleted_count > 0:
                print("Note: No active emails were found, but inactive emails were deleted.")
        else:
            print(f"Total emails purged: {self.deleted_count}")
        print("="*50)
        
    def cleanup(self):
        """Clean up message only"""
        print("Script finished.")
            
    def run(self):
        """Main execution flow"""
        try:
            self.setup_driver()
            self.login_to_icloud()
            self.open_hide_my_email()
            
            # Main operation loop
            while True:
                self.select_mode()
                
                # Skip further processing if preview mode was selected
                if self.mode is None:
                    # Ask if user wants to continue
                    print("\n" + "="*50)
                    continue_choice = self.get_user_input(
                        "Would you like to perform another operation? (yes/no): ",
                        ['yes', 'y', 'no', 'n']
                    )
                    
                    if continue_choice in ['no', 'n']:
                        print("Thank you for using Hide My Email Manager!")
                        print("You can close the browser window manually.")
                        break
                        
                    print("\n" + "="*50)
                    print("Returning to main menu...")
                    print("="*50 + "\n")
                    continue
                
                self.setup_search_filter()
                
                # Execute based on mode
                if self.mode == '1' or self.mode == '3':
                    self.deactivate_emails()
                    
                    if self.original_mode == '3':
                        self.run_purge_transition()
                        self.delete_emails()
                        self.show_purge_summary()
                        
                elif self.mode == '2':
                    self.delete_emails()
                
                # Ask if user wants to continue
                print("\n" + "="*50)
                continue_choice = self.get_user_input(
                    "Would you like to perform another operation? (yes/no): ",
                    ['yes', 'y', 'no', 'n']
                )
                
                if continue_choice in ['no', 'n']:
                    print("Thank you for using Hide My Email Manager!")
                    print("You can close the browser window manually.")
                    break
                    
                print("\n" + "="*50)
                print("Returning to main menu...")
                print("="*50 + "\n")
                
                # Reset for next operation
                self.mode = None
                self.original_mode = None
                self.search_term = None
                self.deactivated_count = 0
                self.deleted_count = 0
                self.is_purge_mode = False
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Script interrupted by user (Ctrl+C)")
            print("Script terminated. You can close the browser window manually.")
        except TimeoutException as e:
            print("\n--- ERROR ---")
            print("The script timed out waiting for an element to appear.")
            print(f"Error details: {e}")
            print("You can close the browser window manually.")
        except Exception as e:
            print(f"\n--- ERROR ---")
            print(f"An unexpected error occurred: {e}")
            print("You can close the browser window manually.")


def main():
    """Entry point"""
    manager = EmailManager()
    manager.run()


if __name__ == "__main__":
    main()