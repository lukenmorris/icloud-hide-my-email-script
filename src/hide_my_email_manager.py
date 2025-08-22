"""
iCloud Hide My Email Manager
A tool to automate deactivation and deletion of Hide My Email addresses
"""

import time
import os
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# Suppress logs
os.environ['WDM_LOG'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


# ============= Configuration =============
ICLOUD_URL = "https://www.icloud.com/icloudplus/"
WAIT_TIMEOUT = 20
LOGIN_TIMEOUT = 300
PROCESS_DELAY = 2  # Delay between processing emails
SEARCH_DELAY = 2   # Delay after applying search
DISPLAY_LIMITS = [20, 50]  # Options for preview display
RATE_DISPLAY_INTERVAL = 5  # Show rate every N emails
ESTIMATED_TIME_PER_EMAIL = 3  # Seconds

# UI Constants
SEPARATOR_WIDTH = 60
DETAIL_SEPARATOR_WIDTH = 80
MAX_PREVIEW_ITEMS = 50
MAX_SUMMARY_ITEMS = 10
PURGE_PREVIEW_LIMIT = 25


class Mode(Enum):
    """Operation modes"""
    DEACTIVATE = '1'
    DELETE = '2'
    PURGE = '3'
    PREVIEW = '4'
    EXIT = '5'


class Section(Enum):
    """Email sections"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'


@dataclass
class EmailItem:
    """Represents an email item"""
    address: str
    label: Optional[str] = None
    
    @property
    def display_name(self):
        """Get formatted display name"""
        if self.label:
            return f"{self.address} → {self.label}"
        return self.address


# XPaths configuration
XPATHS = {
    Section.ACTIVE.value: {
        'header': "/html/body/aside/div/div[1]/div/div/div[2]/section[1]/div/div/div[1]/h2",
        'container': "/html/body/aside/div/div[1]/div/div/div[2]/section[1]/div/div/div[2]/div[2]",
        'search_button': "/html/body/aside/div/div[1]/div/div/div[2]/section[1]/div/div/div[1]/div/div[1]/button",
        'search_input': "/html/body/aside/div/div[1]/div/div/div[2]/section[1]/div/div/div[2]/div[1]/div/input"
    },
    Section.INACTIVE.value: {
        'header': "/html/body/aside/div/div[1]/div/div/div[2]/section[3]/div/div[1]/h2",
        'container': "/html/body/aside/div/div[1]/div/div/div[2]/section[3]/div",
        'search_button': "/html/body/aside/div/div[1]/div/div/div[2]/section[3]/div/div[1]/div/div/button",
        'search_input': "/html/body/aside/div/div[1]/div/div/div[2]/section[3]/div/div[2]/div[1]/div/input"
    }
}


class UIHelper:
    """Helper class for UI operations"""
    
    @staticmethod
    def print_header(title: str, width: int = SEPARATOR_WIDTH, icon: str = ""):
        """Print a formatted header"""
        print("\n" + "=" * width)
        if icon:
            print(f"{icon}  {title}")
        else:
            print(title)
        print("=" * width)
    
    @staticmethod
    def print_separator(width: int = SEPARATOR_WIDTH):
        """Print a separator line"""
        print("-" * width)
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """Format seconds into human-readable time"""
        if seconds < 60:
            return f"{seconds:.0f} seconds"
        elif seconds < 3600:
            return f"{seconds/60:.1f} minutes"
        else:
            return f"{seconds/3600:.1f} hours"
    
    @staticmethod
    def get_user_confirmation(prompt: str, valid_options: List[str]) -> str:
        """Get validated user input"""
        while True:
            response = input(prompt).lower()
            if response in valid_options:
                return response
            print(f"Invalid input. Please enter one of: {', '.join(valid_options)}")


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
        self.ui = UIHelper()
        
    # ============= Driver Setup =============
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with options"""
        print("Configuring Chrome options...")
        chrome_options = self._get_chrome_options()
        
        print("Setting up Chrome driver...")
        service = ChromeService(ChromeDriverManager().install())
        service.log_path = os.devnull
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
    
    def _get_chrome_options(self, headless: bool = False) -> Options:
        """Get Chrome options configuration"""
        chrome_options = Options()
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            if os.name == 'nt':
                chrome_options.add_argument("--disable-console")
                
        return chrome_options
    
    def switch_to_headless(self):
        """Switch from regular to headless mode"""
        try:
            # Save state
            current_url = self.driver.current_url
            cookies = self.driver.get_cookies()
            
            # Recreate driver
            self.driver.quit()
            print("Setting up headless Chrome driver...")
            
            chrome_options = self._get_chrome_options(headless=True)
            service = ChromeService(ChromeDriverManager().install())
            service.log_path = os.devnull
            
            if os.name == 'nt':
                service.creation_flags = 0x08000000  # CREATE_NO_WINDOW
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Restore state
            self.driver.get(current_url)
            self._restore_cookies(cookies)
            self.driver.refresh()
            
            # Verify login
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "icloud-plus-page-route"))
            )
            
            print("✅ Successfully switched to headless mode!")
            self.headless_mode = True
            
        except Exception as e:
            print(f"⚠️ Failed to switch to headless mode: {e}")
            print("Falling back to visible mode...")
            self.setup_driver()
            self.driver.get(current_url)
            self._restore_cookies(cookies)
            self.driver.refresh()
    
    def _restore_cookies(self, cookies: List[dict]):
        """Restore cookies to maintain session"""
        for cookie in cookies:
            if 'sameSite' in cookie:
                del cookie['sameSite']
            try:
                self.driver.add_cookie(cookie)
            except:
                pass
    
    # ============= Navigation =============
    
    def login_to_icloud(self):
        """Navigate to iCloud and handle login process"""
        print(f"Navigating to {ICLOUD_URL}...")
        self.driver.get(ICLOUD_URL)
        
        print("Looking for the initial 'Sign In' button...")
        initial_sign_in = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "sign-in-button"))
        )
        initial_sign_in.click()
        print("Clicked initial 'Sign In' button.")
        
        self.ui.print_header(">>> ACTION REQUIRED <<<")
        print("Please complete the login process in the browser window.")
        print("The script will automatically continue once you land on the iCloud+ Features page.")
        print("=" * SEPARATOR_WIDTH + "\n")
        
        WebDriverWait(self.driver, LOGIN_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "icloud-plus-page-route"))
        )
        print("✅ Login successful! iCloud+ Features page detected.")
        
        self.prompt_headless_mode()
    
    def prompt_headless_mode(self):
        """Ask user if they want to switch to headless mode"""
        self.ui.print_header("HEADLESS MODE OPTION")
        print("Headless mode runs the browser in the background (no visible window).")
        print("This can be less distracting and may run slightly faster.")
        print("Note: You won't be able to see what's happening.")
        print("=" * SEPARATOR_WIDTH)
        
        if self.ui.get_user_confirmation(
            "Would you like to switch to headless mode? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        ) in ['yes', 'y']:
            print("Switching to headless mode...")
            self.switch_to_headless()
        else:
            print("Continuing with visible browser window...")
    
    def open_hide_my_email(self):
        """Open the Hide My Email modal"""
        print("Looking for the 'Hide My Email' tile...")
        hide_my_email = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//article[@aria-label='Hide My Email']"))
        )
        hide_my_email.click()
        print("Successfully clicked the 'Hide My Email' tile.")
        
        print("Waiting for the 'Hide My Email' modal to appear...")
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@data-name='hidemyemail']"))
        )
        print("Successfully switched to the 'Hide My Email' modal.")
    
    def reset_hide_my_email(self):
        """Reset the Hide My Email interface"""
        print("Resetting Hide My Email interface...")
        
        try:
            self.driver.switch_to.default_content()
            self.driver.get(ICLOUD_URL)
            
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "icloud-plus-page-route"))
            )
            
            print("Re-opening Hide My Email...")
            hide_my_email = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//article[@aria-label='Hide My Email']"))
            )
            hide_my_email.click()
            
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@data-name='hidemyemail']"))
            )
            
            print("Hide My Email interface reset successfully.")
            time.sleep(2)
            
        except Exception as e:
            print(f"Error resetting interface: {e}")
            print("Attempting alternative reset method...")
            try:
                self.driver.refresh()
                time.sleep(3)
                WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                    EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@data-name='hidemyemail']"))
                )
            except:
                print("Reset failed. You may need to manually refresh the page.")
    
    # ============= Mode Selection =============
    
    def select_mode(self):
        """Get operation mode from user"""
        mode_text = self.ui.get_user_confirmation(
            "Select a mode:\n"
            "1. Deactivate active emails\n"
            "2. Permanently delete inactive emails\n"
            "3. Purge mode (deactivate then delete)\n"
            "4. Preview mode (view emails without changes)\n"
            "5. Exit\n"
            "Enter choice (1, 2, 3, 4, or 5): ",
            [m.value for m in Mode]
        )
        
        mode = Mode(mode_text)
        
        if mode == Mode.EXIT:
            print("Exiting... Thank you for using Hide My Email Manager!")
            print("You can close the browser window manually.")
            exit()
        
        self.mode = mode.value
        self.original_mode = mode.value
        
        if mode == Mode.PURGE:
            self.handle_purge_confirmation()
        elif mode == Mode.PREVIEW:
            self.preview_mode()
    
    def setup_search_filter(self):
        """Setup search filtering if needed"""
        if self.mode != Mode.PURGE.value:
            use_search = self.ui.get_user_confirmation(
                "Do you want to filter by a specific search term?\n"
                "(Searches both email addresses and labels/notes)\n"
                "Enter (yes/no): ",
                ['yes', 'y', 'no', 'n']
            )
            
            if use_search in ['yes', 'y']:
                self.search_term = self.get_search_term()
                print(f"Search term set: '{self.search_term}'")
            else:
                print("No search filter will be applied - processing all emails...")
    
    def get_search_term(self) -> str:
        """Get search term from user"""
        while True:
            term = input("Enter the search term for emails to filter/purge: ").strip()
            if term:
                print(f"Will filter for emails containing '{term}'...")
                return term
            print("Search term cannot be empty.")
    
    # ============= Email Operations =============
    
    def apply_search_filter(self, section: str, search_term: Optional[str] = None):
        """Apply search filter to specified section"""
        term_to_use = search_term if search_term is not None else self.search_term
        
        if not term_to_use:
            return
        
        print(f"Applying search filter '{term_to_use}' to {section} section...")
        
        search_button = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, XPATHS[section]['search_button']))
        )
        search_button.click()
        
        search_input = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, XPATHS[section]['search_input']))
        )
        search_input.clear()
        search_input.send_keys(term_to_use)
        time.sleep(SEARCH_DELAY)
    
    def get_email_count(self, section: str) -> Tuple[str, int, List]:
        """Get count of emails in the specified section"""
        try:
            header = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, XPATHS[section]['header']))
            )
            header_text = header.text
            
            # Extract count from header
            if 'no' in header_text.lower():
                total_count = "0"
            else:
                total_count = header_text.split()[0]
            
            # Get items
            try:
                container = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, XPATHS[section]['container']))
                )
                items = container.find_elements(By.XPATH, ".//li[contains(@class, 'card-list-item-platter')]")
            except TimeoutException:
                print(f"Using fallback method to find {section} emails...")
                section_num = '1' if section == Section.ACTIVE.value else '3'
                items = self.driver.find_elements(
                    By.XPATH, f"//section[{section_num}]//li[contains(@class, 'card-list-item-platter')]"
                )
            
            return total_count, len(items), items if items else []
            
        except Exception as e:
            print(f"Error getting {section} email count: {e}")
            return "0", 0, []
    
    def get_email_details(self, item) -> Tuple[Optional[str], Optional[str]]:
        """Get both email address and label from an item"""
        try:
            email_address = item.find_element(By.CLASS_NAME, "searchable-card-subtitle").text
            
            label = ""
            source = ""
            
            try:
                label_element = item.find_element(By.CSS_SELECTOR, ".card-title h2.Typography")
                label = label_element.text
                
                try:
                    source_element = item.find_element(By.CSS_SELECTOR, ".card-title span.Typography")
                    source = source_element.text
                except:
                    pass
                    
            except:
                try:
                    card_title = item.find_element(By.CLASS_NAME, "card-title")
                    label = card_title.text.split('\n')[0] if card_title.text else ""
                except:
                    pass
            
            full_label = f"{label} ({source})" if label and source else label
            return email_address, full_label
            
        except:
            return None, None
    
    def collect_email_items(self, items: List) -> List[EmailItem]:
        """Collect EmailItem objects from DOM elements"""
        email_items = []
        for item in items:
            address, label = self.get_email_details(item)
            if address:
                email_items.append(EmailItem(address, label))
        return email_items
    
    def process_email_item(self, item, action: str) -> Tuple[bool, Optional[str]]:
        """Process a single email item (deactivate or delete)"""
        try:
            email_address, label = self.get_email_details(item)
            if not email_address:
                return False, None
            
            email = EmailItem(email_address, label)
            print(f"Processing: {email.display_name}")
            
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
            
            print(f"--> {action.capitalize()[:-1]}ing {email.display_name}...")
            self.driver.execute_script("arguments[0].click();", confirm_button)
            
            WebDriverWait(self.driver, 15).until(
                EC.invisibility_of_element_located((By.XPATH, confirm_xpath))
            )
            
            return True, email.display_name
            
        except TimeoutException:
            print(f"Error: No '{button_text}' button found. Stopping.")
            return False, None
        except Exception as e:
            print(f"Error processing email: {e}")
            return False, None
    
    # ============= Preview Mode =============
    
    def preview_mode(self):
        """Preview emails without making any changes"""
        self.ui.print_header("📋 PREVIEW MODE", icon="📋")
        print("This mode shows emails without making any changes.")
        print("=" * SEPARATOR_WIDTH + "\n")
        
        section_choice = self.ui.get_user_confirmation(
            "Which emails would you like to preview?\n"
            "1. Active emails\n"
            "2. Inactive emails\n"
            "3. Both\n"
            "Enter choice (1, 2, or 3): ",
            ['1', '2', '3']
        )
        
        use_search = self.ui.get_user_confirmation(
            "Do you want to filter by a search term? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        )
        
        search_term = None
        if use_search in ['yes', 'y']:
            search_term = input("Enter search term: ").strip()
        
        if section_choice in ['1', '3']:
            self.preview_section(Section.ACTIVE.value, search_term)
        
        if section_choice in ['2', '3']:
            self.preview_section(Section.INACTIVE.value, search_term)
        
        self.ui.print_header("Preview complete. No changes were made.")
        self.mode = None
    
    def preview_section(self, section: str, search_term: Optional[str] = None):
        """Preview emails in a specific section"""
        self.ui.print_header(f"📧 {section.upper()} EMAILS", width=50, icon="📧")
        
        if search_term:
            print(f"Applying filter: '{search_term}'...")
            self.apply_search_filter(section, search_term)
        
        total, relevant, items = self.get_email_count(section)
        
        if search_term:
            print(f"\nFound {relevant} {section} emails matching '{search_term}' (Total {section}: {total})")
        else:
            print(f"\nTotal {section} emails: {relevant}")
        
        if relevant == 0:
            print(f"No {section} emails found.")
            return
        
        display_count = self._get_display_count(relevant)
        email_items = self.collect_email_items(items[:display_count])
        
        self._display_email_list(email_items, relevant)
        
        if len(email_items) >= 10:
            self._show_email_summaries(email_items)
    
    def _get_display_count(self, total: int) -> int:
        """Get number of items to display based on total"""
        if total <= DISPLAY_LIMITS[0]:
            return total
        
        print(f"\nFound {total} emails. How many would you like to see?")
        options = []
        for i, limit in enumerate(DISPLAY_LIMITS, 1):
            if total > limit:
                options.append(str(i))
                print(f"{i}. First {limit}")
        options.append(str(len(options) + 1))
        print(f"{len(options)}. All")
        
        choice = self.ui.get_user_confirmation(
            f"Enter choice ({', '.join(options)}): ",
            options
        )
        
        if int(choice) <= len(DISPLAY_LIMITS):
            return DISPLAY_LIMITS[int(choice) - 1]
        return total
    
    def _display_email_list(self, email_items: List[EmailItem], total: int):
        """Display list of emails"""
        print(f"\nDisplaying {len(email_items)} of {total} emails:")
        self.ui.print_separator(DETAIL_SEPARATOR_WIDTH)
        
        for i, email in enumerate(email_items, 1):
            print(f"{i:3}. {email.display_name}")
            
            if i % 10 == 0:
                time.sleep(0.5)
        
        self.ui.print_separator(DETAIL_SEPARATOR_WIDTH)
        print(f"Displayed {len(email_items)} of {total} emails")
    
    def _show_email_summaries(self, email_items: List[EmailItem]):
        """Show summaries of emails by service and label"""
        services = {}
        labels = {}
        
        for email in email_items:
            # Count by service
            if '@' in email.address:
                prefix = email.address.split('@')[0]
                parts = prefix.split('.')
                service = parts[-1] if parts else prefix
                services[service] = services.get(service, 0) + 1
            
            # Count by label
            if email.label:
                main_label = email.label.split('(')[0].strip()
                if main_label:
                    labels[main_label] = labels.get(main_label, 0) + 1
        
        if services:
            print("\n📊 Summary by service:")
            for service, count in sorted(services.items(), key=lambda x: x[1], reverse=True)[:MAX_SUMMARY_ITEMS]:
                print(f"   • {service}: {count} email{'s' if count > 1 else ''}")
        
        if labels:
            print("\n🏷️  Summary by label:")
            for label, count in sorted(labels.items(), key=lambda x: x[1], reverse=True)[:MAX_SUMMARY_ITEMS]:
                print(f"   • {label}: {count} email{'s' if count > 1 else ''}")
    
    # ============= Operations =============
    
    def preview_and_confirm_operation(self, section: str, action: str, search_term: Optional[str] = None) -> bool:
        """Preview emails that will be affected and get confirmation"""
        self.ui.print_header("⚠️  OPERATION PREVIEW", icon="⚠️")
        
        action_text = {
            'deactivate': 'DEACTIVATED',
            'delete': 'PERMANENTLY DELETED',
            'purge': 'PURGED (deactivated then deleted)'
        }[action]
        
        print(f"The following emails will be {action_text}:")
        print("=" * SEPARATOR_WIDTH + "\n")
        
        term_to_use = search_term if search_term is not None else self.search_term
        
        if term_to_use:
            self.apply_search_filter(section, term_to_use)
        
        total, relevant, items = self.get_email_count(section)
        
        if relevant == 0:
            print(f"No {section} emails found{f' matching {term_to_use}' if term_to_use else ''}.")
            return False
        
        email_items = self.collect_email_items(items)
        
        # Display preview
        print(f"📋 Emails to be {action_text.lower()}: {len(email_items)} total")
        
        if term_to_use:
            print(f"🔍 Filter applied: '{term_to_use}' (searches emails and labels)")
        
        print("\n" + "-" * 50)
        
        for i, email in enumerate(email_items[:MAX_PREVIEW_ITEMS], 1):
            print(f"{i:3}. {email.display_name}")
        
        if len(email_items) > MAX_PREVIEW_ITEMS:
            print(f"\n... and {len(email_items) - MAX_PREVIEW_ITEMS} more emails")
        
        print("-" * 50)
        
        if len(email_items) >= 5:
            self._show_email_summaries(email_items)
        
        # Final confirmation
        self.ui.print_header("⚠️  FINAL CONFIRMATION REQUIRED ⚠️", icon="⚠️")
        print(f"You are about to {action} {len(email_items)} email{'s' if len(email_items) > 1 else ''}.")
        
        if action in ['delete', 'purge']:
            print("❗ This action is PERMANENT and cannot be undone!")
        
        print("=" * SEPARATOR_WIDTH + "\n")
        
        if len(email_items) > 20:
            print(f"⚠️  WARNING: This is a large operation ({len(email_items)} emails)")
            estimated_time = len(email_items) * ESTIMATED_TIME_PER_EMAIL
            print(f"⏱️  Estimated time: {self.ui.format_time(estimated_time)}\n")
        
        confirm = self.ui.get_user_confirmation(
            f"Do you want to proceed with {action} operation? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        )
        
        if confirm in ['yes', 'y']:
            print(f"\n✅ Confirmed. Starting {action} operation...")
            print("=" * SEPARATOR_WIDTH + "\n")
            return True
        else:
            print(f"\n❌ Operation cancelled. No emails were {action_text.lower()}.")
            return False
    
    def _process_emails_loop(self, section: str, action: str) -> int:
        """Main loop for processing emails"""
        processed_count = 0
        self.operation_start_time = time.time()
        initial_total = None
        
        mode_indicator = " (HEADLESS MODE)" if self.headless_mode else ""
        print(f"Starting {action} process{mode_indicator}...")
        
        while True:
            try:
                total, relevant, items = self.get_email_count(section)
                
                if initial_total is None:
                    initial_total = relevant
                
                # Display progress
                if self.search_term:
                    print(f"\nRemaining {section} emails matching '{self.search_term}': {relevant} (Total {section}: {total})")
                else:
                    print(f"\nRemaining {section} emails: {relevant}")
                
                if processed_count > 0 and initial_total > 0:
                    self._display_progress(processed_count, initial_total)
                
                # Check if done
                if total in ["0", "no"] or relevant == 0:
                    if self.search_term and relevant == 0:
                        print(f"No {section} emails found matching '{self.search_term}'.")
                    else:
                        print(f"No {section} emails remaining.")
                    break
                
                if not items:
                    print(f"No more {section} emails found to process.")
                    break
                
                # Process first item
                success, email_name = self.process_email_item(items[0], action)
                if success:
                    processed_count += 1
                    print(f"✅ Successfully {action}d email #{processed_count}: {email_name}")
                    
                    if processed_count % RATE_DISPLAY_INTERVAL == 0:
                        self._display_rate(processed_count)
                    
                    time.sleep(PROCESS_DELAY)
                    
                    if self.search_term:
                        self.apply_search_filter(section)
                else:
                    break
                    
            except (TimeoutException, IndexError):
                print(f"No more {section} email addresses found.")
                break
            except StaleElementReferenceException:
                print("Page structure changed. Re-searching for elements...")
                continue
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Stopping to prevent processing wrong emails.")
                break
        
        return processed_count
    
    def _display_progress(self, processed: int, total: int):
        """Display progress information"""
        progress_pct = (processed / total) * 100
        elapsed = self.ui.format_time(time.time() - self.operation_start_time)
        eta = self._estimate_time_remaining(processed, total)
        print(f"Progress: {processed}/{total} ({progress_pct:.1f}%) | Elapsed: {elapsed} | ETA: {eta}")
    
    def _display_rate(self, processed: int):
        """Display processing rate"""
        elapsed = time.time() - self.operation_start_time
        if elapsed > 0:
            rate = (processed / elapsed) * 60
            print(f"   📊 Rate: {rate:.1f} emails/minute")
    
    def _estimate_time_remaining(self, processed: int, total: int) -> str:
        """Estimate time remaining"""
        if processed == 0:
            return "Calculating..."
        
        elapsed = time.time() - self.operation_start_time
        if elapsed < 1:
            return "Calculating..."
        
        rate = processed / elapsed
        remaining = total - processed
        eta_seconds = remaining / rate if rate > 0 else 0
        
        return self.ui.format_time(eta_seconds)
    
    def _display_operation_summary(self, action: str, count: int):
        """Display operation summary"""
        if count > 0:
            total_time = self.ui.format_time(time.time() - self.operation_start_time)
            print(f"\n✅ {action.capitalize()} complete!")
            print(f"   • Total {action}d: {count}")
            print(f"   • Time taken: {total_time}")
            
            if self.operation_start_time:
                elapsed = time.time() - self.operation_start_time
                if elapsed > 0:
                    rate = (count / elapsed) * 60
                    print(f"   • Average rate: {rate:.1f} emails/minute")
        else:
            print(f"\n✅ {action.capitalize()} complete. No emails were {action}d.")
    
    def deactivate_emails(self):
        """Deactivate active emails"""
        if self.is_purge_mode:
            if not self.preview_purge_operation():
                self.deactivated_count = 0
                return
        else:
            if not self.preview_and_confirm_operation(Section.ACTIVE.value, 'deactivate', self.search_term):
                self.deactivated_count = 0
                return
        
        self.deactivated_count = self._process_emails_loop(Section.ACTIVE.value, 'deactivate')
        self._display_operation_summary('deactivate', self.deactivated_count)
    
    def delete_emails(self):
        """Delete inactive emails"""
        if not self.is_purge_mode:
            if not self.preview_and_confirm_operation(Section.INACTIVE.value, 'delete', self.search_term):
                self.deleted_count = 0
                return
        
        self.deleted_count = self._process_emails_loop(Section.INACTIVE.value, 'delete')
        self._display_operation_summary('delete', self.deleted_count)
    
    # ============= Purge Mode =============
    
    def handle_purge_confirmation(self):
        """Handle confirmation for purge mode"""
        self.ui.print_header("⚠️  PURGE MODE WARNING ⚠️", icon="⚠️")
        print("Purge mode will:")
        print("1. Deactivate active emails")
        print("2. Then permanently DELETE those emails")
        print("This action cannot be undone!")
        print("=" * SEPARATOR_WIDTH)
        
        if self.ui.get_user_confirmation(
            "Are you sure you want to proceed with PURGE mode? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        ) in ['no', 'n']:
            print("Purge mode cancelled. Exiting script.")
            exit()
        
        print("Purge mode confirmed. Proceeding...")
        
        if self.ui.get_user_confirmation(
            "Do you want to filter by a specific search term? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        ) in ['yes', 'y']:
            self.search_term = self.get_search_term()
        else:
            self.confirm_purge_all()
    
    def confirm_purge_all(self):
        """Extra confirmation for purging all emails"""
        self.ui.print_header("⚠️⚠️⚠️  EXTREME WARNING ⚠️⚠️⚠️", icon="⚠️⚠️⚠️")
        print("You are about to purge ALL emails!")
        print("This will:")
        print("1. Deactivate ALL active Hide My Email addresses")
        print("2. Permanently DELETE ALL Hide My Email addresses")
        print("This is IRREVERSIBLE!")
        print("=" * SEPARATOR_WIDTH)
        
        if self.ui.get_user_confirmation(
            "Are you ABSOLUTELY SURE you want to purge ALL emails? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        ) in ['no', 'n']:
            print("Purge all cancelled. Exiting script.")
            exit()
        
        print("Purging ALL emails confirmed. Proceeding...")
    
    def preview_purge_operation(self) -> bool:
        """Preview both active and inactive emails for purge operation"""
        self.ui.print_header("⚠️  PURGE OPERATION PREVIEW", icon="⚠️")
        print("The following emails will be PURGED (deactivated then deleted):")
        print("=" * SEPARATOR_WIDTH + "\n")
        
        # Get active emails
        if self.search_term:
            self.apply_search_filter(Section.ACTIVE.value, self.search_term)
        
        active_total, active_relevant, active_items = self.get_email_count(Section.ACTIVE.value)
        active_emails = self.collect_email_items(active_items)
        
        # Get inactive emails
        if self.search_term:
            self.apply_search_filter(Section.INACTIVE.value, self.search_term)
        
        inactive_total, inactive_relevant, inactive_items = self.get_email_count(Section.INACTIVE.value)
        inactive_emails = self.collect_email_items(inactive_items)
        
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
        
        self.ui.print_separator()
        
        # Show emails
        if active_emails:
            print("\n🟢 ACTIVE emails (will be deactivated first):")
            for i, email in enumerate(active_emails[:PURGE_PREVIEW_LIMIT], 1):
                print(f"   {i:3}. {email.display_name}")
            if len(active_emails) > PURGE_PREVIEW_LIMIT:
                print(f"   ... and {len(active_emails) - PURGE_PREVIEW_LIMIT} more active emails")
        
        if inactive_emails:
            print("\n🔴 INACTIVE emails (will be permanently deleted):")
            for i, email in enumerate(inactive_emails[:PURGE_PREVIEW_LIMIT], 1):
                print(f"   {i:3}. {email.display_name}")
            if len(inactive_emails) > PURGE_PREVIEW_LIMIT:
                print(f"   ... and {len(inactive_emails) - PURGE_PREVIEW_LIMIT} more inactive emails")
        
        self.ui.print_separator()
        
        # Final confirmation
        self.ui.print_header("⚠️⚠️  FINAL PURGE CONFIRMATION  ⚠️⚠️", icon="⚠️⚠️")
        print(f"You are about to PERMANENTLY PURGE {total_affected} email{'s' if total_affected > 1 else ''}:")
        print(f"   • {len(active_emails)} will be deactivated")
        print(f"   • {total_affected} will be permanently deleted")
        print("\n❗❗ This action is IRREVERSIBLE! ❗❗")
        print("=" * SEPARATOR_WIDTH + "\n")
        
        if total_affected > 20:
            estimated_time = total_affected * ESTIMATED_TIME_PER_EMAIL
            print(f"⚠️  WARNING: Large operation ({total_affected} emails)")
            print(f"⏱️  Estimated time: {self.ui.format_time(estimated_time)}\n")
        
        confirm = self.ui.get_user_confirmation(
            f"Are you ABSOLUTELY SURE you want to PURGE {total_affected} emails? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        )
        
        if confirm in ['yes', 'y']:
            print(f"\n✅ Purge confirmed. Starting operation...")
            print("=" * SEPARATOR_WIDTH + "\n")
            return True
        else:
            print(f"\n❌ Purge cancelled. No emails were affected.")
            return False
    
    def run_purge_transition(self):
        """Transition from deactivation to deletion in purge mode"""
        self.ui.print_header("Proceeding to deletion phase of purge...")
        if self.deactivated_count == 0:
            print("No active emails were found, but checking for inactive emails...")
        print("=" * SEPARATOR_WIDTH + "\n")
        time.sleep(3)
        
        if self.search_term:
            self.apply_search_filter(Section.INACTIVE.value)
        else:
            print("Proceeding to delete ALL inactive emails...")
        
        self.mode = Mode.DELETE.value
    
    def show_purge_summary(self):
        """Show summary for purge mode"""
        self.ui.print_header("🗑️  PURGE COMPLETE!")
        print(f"Emails deactivated: {self.deactivated_count}")
        print(f"Emails deleted: {self.deleted_count}")
        
        if self.search_term:
            print(f"Total emails purged for '{self.search_term}': {self.deleted_count}")
            if self.deactivated_count == 0 and self.deleted_count > 0:
                print("Note: No active emails were found, but inactive emails were deleted.")
        else:
            print(f"Total emails purged: {self.deleted_count}")
        print("=" * SEPARATOR_WIDTH)
    
    # ============= Main Loop =============
    
    def run(self):
        """Main execution flow"""
        try:
            self.setup_driver()
            self.login_to_icloud()
            self.open_hide_my_email()
            
            while True:
                self.select_mode()
                
                if self.mode is None:  # Preview mode was selected
                    if not self._ask_continue():
                        break
                    self.reset_hide_my_email()
                    continue
                
                self.setup_search_filter()
                
                # Execute based on mode
                if self.mode == Mode.DEACTIVATE.value or self.mode == Mode.PURGE.value:
                    if self.mode == Mode.PURGE.value:
                        self.is_purge_mode = True
                    self.deactivate_emails()
                    
                    if self.original_mode == Mode.PURGE.value:
                        self.run_purge_transition()
                        self.delete_emails()
                        self.show_purge_summary()
                
                elif self.mode == Mode.DELETE.value:
                    self.delete_emails()
                
                if not self._ask_continue():
                    break
                
                self.reset_hide_my_email()
                self._reset_state()
                
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
    
    def _ask_continue(self) -> bool:
        """Ask if user wants to continue"""
        self.ui.print_header("")
        response = self.ui.get_user_confirmation(
            "Would you like to perform another operation? (yes/no): ",
            ['yes', 'y', 'no', 'n']
        )
        
        if response in ['no', 'n']:
            print("Script finished.")
            print("You can close the browser window manually.")
            return False
        
        self.ui.print_header("Returning to main menu...")
        return True
    
    def _reset_state(self):
        """Reset state for next operation"""
        self.mode = None
        self.original_mode = None
        self.search_term = None
        self.deactivated_count = 0
        self.deleted_count = 0
        self.is_purge_mode = False


def main():
    """Entry point"""
    manager = EmailManager()
    manager.run()


if __name__ == "__main__":
    main()