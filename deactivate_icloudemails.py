# main.py
# Import necessary libraries
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
# Direct URL to the iCloud+ Features page
ICLOUD_URL = "https://www.icloud.com/icloudplus/"

# --- Main Script ---

# 1. Set up Chrome options
print("Configuring Chrome options...")
chrome_options = Options()
chrome_options.add_argument("--log-level=3")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

# 2. Initialize the Chrome WebDriver
print("Setting up Chrome driver...")
driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=chrome_options
)

try:
    # 3. Navigate to the specific iCloud+ page
    print(f"Navigating to {ICLOUD_URL}...")
    driver.get(ICLOUD_URL)

    # 3a. Click the initial "Sign In" button on the landing page.
    print("Looking for the initial 'Sign In' button...")
    initial_sign_in_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "sign-in-button"))
    )
    initial_sign_in_button.click()
    print("Clicked initial 'Sign In' button.")

    # 4. Instruct user to log in manually
    print("\n" + "="*50)
    print(">>> ACTION REQUIRED <<<")
    print("Please complete the login process in the browser window.")
    print("The script will automatically continue once you land on the iCloud+ Features page.")
    print("="*50 + "\n")

    # 5. Wait for the user to land on the iCloud+ Features page
    WebDriverWait(driver, 300).until( # Wait for up to 5 minutes
        EC.presence_of_element_located((By.CLASS_NAME, "icloud-plus-page-route"))
    )
    print("✅ Login successful! iCloud+ Features page detected.")
    
    # 6. Find and click the "Hide My Email" tile
    print("Looking for the 'Hide My Email' tile...")
    hide_my_email_tile = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//article[@aria-label='Hide My Email']"))
    )
    hide_my_email_tile.click()
    print("Successfully clicked the 'Hide My Email' tile.")

    # 7. Switch to the Hide My Email iframe that has appeared
    print("Waiting for the 'Hide My Email' modal to appear...")
    WebDriverWait(driver, 20).until(
        EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@data-name='hidemyemail']"))
    )
    print("Successfully switched to the 'Hide My Email' modal.")

    # 8. Handle optional search
    search_term = None # Initialize search_term
    use_search = input("Do you want to delete emails containing a specific search term? (yes/no): ").lower()
    if use_search in ['yes', 'y']:
        search_term = input("What term would you like to search for?: ")
        print(f"Searching for emails containing '{search_term}'...")
        
        search_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='Search']"))
        )
        search_button.click()
        
        search_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "form-textbox-input"))
        )
        search_input.send_keys(search_term)
        print("Search term entered. Waiting for results to filter...")
        time.sleep(3) # Wait for search results to filter

        # Count the emails that match the search criteria
        active_list_xpath = "//div[.//h2[contains(text(), 'active email addresses')]]/following-sibling::div//li[contains(@class, 'card-list-item-platter')]"
        filtered_emails = driver.find_elements(By.XPATH, active_list_xpath)
        print(f"Found {len(filtered_emails)} active email(s) matching your search.")

    else:
        print("Proceeding without a search filter.")

    # 9. Main deactivation loop
    print("\nStarting deactivation process...")
    deactivated_count = 0
    while True:
        try:
            # Find the header to get the count for logging
            try:
                header_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'active email addresses')]"))
                )
                header_text = header_element.text
                email_count_from_text = header_text.split()[0]
                print(f"Remaining active emails: {email_count_from_text}")
            except:
                # If the header isn't found, it likely means there are no active emails left.
                print("Could not find the 'active email addresses' header. Assuming process is complete.")
                break

            # Find the actual list of emails to process
            active_list_xpath = "//div[.//h2[contains(text(), 'active email addresses')]]/following-sibling::div//li[contains(@class, 'card-list-item-platter')]"
            email_items = driver.find_elements(By.XPATH, active_list_xpath)
            
            if not email_items:
                print("No more email addresses found to deactivate.")
                break
            
            item = email_items[0]

            expand_button = item.find_element(By.CLASS_NAME, "button-expand")
            driver.execute_script("arguments[0].click();", expand_button)
            time.sleep(2)

            deactivate_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Deactivate email address']"))
            )
            driver.execute_script("arguments[0].click();", deactivate_button)
            
            time.sleep(1)
            confirm_button_xpath = "//button[.//span[text()='Deactivate']]"
            confirm_deactivate_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, confirm_button_xpath))
            )
            driver.execute_script("arguments[0].click();", confirm_deactivate_button)
            
            WebDriverWait(driver, 15).until(
                EC.invisibility_of_element_located((By.XPATH, confirm_button_xpath))
            )

            deactivated_count += 1
            print(f"Successfully deactivated email #{deactivated_count}")
            
            time.sleep(2)

            if search_term:
                print("Re-applying search filter...")
                search_button = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@title='Search']"))
                )
                search_button.click()
                
                search_input = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "form-textbox-input"))
                )
                search_input.clear()
                search_input.send_keys(search_term)
                time.sleep(3)

        except StaleElementReferenceException:
            print("Page refreshed. Re-finding email list...")
            continue
        except TimeoutException:
            print("No more active email addresses found.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

    print(f"\n✅ Deactivation complete. Total addresses deactivated: {deactivated_count}")
    time.sleep(3)

except TimeoutException as e:
    print("\n--- ERROR ---")
    print("The script timed out waiting for an element to appear.")
    print(f"Error details: {e}")

finally:
    print("Script finished. Closing browser.")
    driver.quit()
