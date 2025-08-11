"""
iCloud Hide My Email Manager
A tool to automate deactivation and deletion of Hide My Email addresses
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager


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
        
    def setup_driver(self):
        """Initialize Chrome WebDriver with options"""
        print("Configuring Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        print("Setting up Chrome driver...")
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
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
            "Enter choice (1, 2, or 3): ",
            ['1', '2', '3']
        )
        self.mode = mode
        self.original_mode = mode
        
        if mode == '3':
            self.handle_purge_confirmation()
            
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
            self.cleanup()
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
            self.cleanup()
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
            
            return True
            
        except TimeoutException:
            print(f"Error: No '{button_text}' button found. Stopping.")
            return False
        except Exception as e:
            print(f"Error processing email: {e}")
            return False
            
    def deactivate_emails(self):
        """Deactivate active emails"""
        print("\nStarting Deactivation process...")
        processed_count = 0
        
        while True:
            try:
                total, relevant, items = self.get_email_count('active')
                
                # Display count
                if self.search_term:
                    print(f"Remaining active emails matching '{self.search_term}': {relevant} (Total active: {total})")
                else:
                    print(f"Remaining active emails: {relevant}")
                    
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
                if self.process_email_item(items[0], 'deactivate'):
                    processed_count += 1
                    print(f"Successfully deactivated email #{processed_count}")
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
                
        print(f"\n✅ Deactivation complete. Total addresses deactivated: {processed_count}")
        self.deactivated_count = processed_count
        
    def delete_emails(self):
        """Delete inactive emails"""
        print("\nStarting Deletion process...")
        processed_count = 0
        
        while True:
            try:
                total, relevant, items = self.get_email_count('inactive')
                
                # Display count
                if self.search_term:
                    print(f"Remaining inactive emails matching '{self.search_term}': {relevant} (Total inactive: {total})")
                else:
                    print(f"Remaining inactive emails: {relevant}")
                    
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
                if self.process_email_item(items[0], 'delete'):
                    processed_count += 1
                    print(f"Successfully deleted email #{processed_count}")
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
                
        print(f"\n✅ Deletion complete. Total addresses deleted: {processed_count}")
        self.deleted_count = processed_count
        
    def run_purge_transition(self):
        """Transition from deactivation to deletion in purge mode"""
        print("\n" + "="*50)
        print("Proceeding to deletion phase of purge...")
        if self.deactivated_count == 0:
            print("No active emails were found, but checking for inactive emails...")
        print("="*50 + "\n")
        time.sleep(3)
        
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
        """Clean up resources"""
        if self.driver:
            print("Script finished. Closing browser.")
            self.driver.quit()
            
    def run(self):
        """Main execution flow"""
        try:
            self.setup_driver()
            self.login_to_icloud()
            self.open_hide_my_email()
            self.select_mode()
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
                
            time.sleep(10)
            
        except TimeoutException as e:
            print("\n--- ERROR ---")
            print("The script timed out waiting for an element to appear.")
            print(f"Error details: {e}")
        finally:
            self.cleanup()


def main():
    """Entry point"""
    manager = EmailManager()
    manager.run()


if __name__ == "__main__":
    main()