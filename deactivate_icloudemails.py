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

    # 8. Mode and Search Term selection at the beginning
    mode = ""
    while mode not in ['1', '2']:
        mode = input("Select a mode:\n1. Deactivate active emails\n2. Permanently delete inactive emails\nEnter choice (1 or 2): ")

    search_term = None
    search_input_xpath = None
    search_button_xpath = None
    use_search = input("Do you want to filter by a specific search term? (yes/no): ").lower()
    if use_search in ['yes', 'y']:
        search_term = input("What term would you like to search for?: ")
        print(f"Filtering for emails containing '{search_term}'...")
        
        # Use specific XPaths for search based on mode
        if mode == '1':
            search_button_xpath = "/html/body/aside/div/div[1]/div/div/div[2]/section[1]/div/div/div[1]/div/div[1]/button"
            search_input_xpath = "/html/body/aside/div/div[1]/div/div/div[2]/section[1]/div/div/div[2]/div[1]/div/input"
        else: # mode == '2'
            search_button_xpath = "/html/body/aside/div/div[1]/div/div/div[2]/section[3]/div/div[1]/div/div/button"
            search_input_xpath = "/html/body/aside/div/div[1]/div/div/div[2]/section[3]/div/div[2]/div[1]/div/input"

        search_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, search_button_xpath))
        )
        search_button.click()
        
        search_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, search_input_xpath))
        )
        search_input.send_keys(search_term)
        time.sleep(3)

    # --- DEACTIVATION MODE ---
    if mode == '1':
        print("\nStarting Deactivation process...")
        processed_count = 0
        while True:
            try:
                # Get count from header text
                header_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'active email addresses')]"))
                )
                header_text = header_element.text
                email_count_from_text = header_text.split()[0]
                print(f"Remaining active emails: {email_count_from_text}")

                active_list_xpath = "//div[.//h2[contains(text(), 'active email addresses')]]/following-sibling::div//li[contains(@class, 'card-list-item-platter')]"
                email_items = driver.find_elements(By.XPATH, active_list_xpath)
                
                if not email_items:
                    print("No more active emails found to process.")
                    break
                
                item = email_items[0]
                # UPDATED: Get email address for logging
                email_address = item.find_element(By.CLASS_NAME, "searchable-card-subtitle").text
                print(f"Processing: {email_address}")

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
                print(f"--> Deactivating {email_address}...")
                driver.execute_script("arguments[0].click();", confirm_deactivate_button)
                
                WebDriverWait(driver, 15).until(EC.invisibility_of_element_located((By.XPATH, confirm_button_xpath)))
                processed_count += 1
                print(f"Successfully deactivated email #{processed_count}: {email_address}")
                time.sleep(2)

                if search_term:
                    # UPDATED: Re-apply search filter
                    print("Re-applying search filter...")
                    search_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, search_button_xpath))
                    )
                    search_button.click()
                    
                    search_input = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, search_input_xpath)))
                    search_input.clear()
                    search_input.send_keys(search_term)
                    time.sleep(3)

            except (TimeoutException, IndexError):
                print("No more active email addresses found.")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break
        print(f"\n✅ Deactivation complete. Total addresses deactivated: {processed_count}")

    # --- DELETION MODE ---
    elif mode == '2':
        print("\nStarting Deletion process...")
        processed_count = 0
        while True:
            try:
                header_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'inactive email addresses')]"))
                )
                header_text = header_element.text
                email_count_from_text = header_text.split()[0]
                print(f"Remaining inactive emails: {email_count_from_text}")

                inactive_list_xpath = "//div[.//h2[contains(text(), 'inactive email addresses')]]/following-sibling::div//li[contains(@class, 'card-list-item-platter')]"
                email_items = driver.find_elements(By.XPATH, inactive_list_xpath)

                if not email_items:
                    print("No more inactive email addresses found.")
                    break

                item = email_items[0]
                # UPDATED: Get email address for logging
                email_address = item.find_element(By.CLASS_NAME, "searchable-card-subtitle").text
                print(f"Processing: {email_address}")

                expand_button = item.find_element(By.CLASS_NAME, "button-expand")
                driver.execute_script("arguments[0].click();", expand_button)
                time.sleep(2)

                delete_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Delete address']"))
                )
                driver.execute_script("arguments[0].click();", delete_button)
                
                time.sleep(1)
                confirm_button_xpath = "//button[.//span[text()='Delete']]"
                confirm_delete_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, confirm_button_xpath))
                )
                print(f"--> Deleting {email_address}...")
                driver.execute_script("arguments[0].click();", confirm_delete_button)

                WebDriverWait(driver, 15).until(EC.invisibility_of_element_located((By.XPATH, confirm_button_xpath)))
                processed_count += 1
                print(f"Successfully deleted email #{processed_count}: {email_address}")
                time.sleep(2)

                if search_term:
                    # Re-apply search filter
                    print("Re-applying search filter...")
                    search_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, search_button_xpath))
                    )
                    search_button.click()
                    
                    search_input = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, search_input_xpath))
                    )
                    search_input.clear()
                    search_input.send_keys(search_term)
                    time.sleep(3)

            except (TimeoutException, IndexError):
                print("No more inactive email addresses found.")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break
        print(f"\n✅ Deletion complete. Total addresses deleted: {processed_count}")

    time.sleep(10)

except TimeoutException as e:
    print("\n--- ERROR ---")
    print("The script timed out waiting for an element to appear.")
    print(f"Error details: {e}")

finally:
    print("Script finished. Closing browser.")
    driver.quit()
