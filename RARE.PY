from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Setup Chrome options
chrome_options = Options()
# chrome_options.add_argument("--headless")  # TEMPORARILY DISABLED FOR DEBUGGING
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Setup the driver
driver = webdriver.Chrome(service=Service(), options=chrome_options)

# Open the URL
url = "https://rera.odisha.gov.in/projects/project-list"
driver.get(url)
wait = WebDriverWait(driver, 15)

# Scroll to bottom to load all projects
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(5)

projects_data = []

# Wait and check how many buttons are loaded
try:
    view_buttons = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[contains(text(),"View Details")]')))
    print(f"Found {len(view_buttons)} 'View Details' buttons.")
except Exception as e:
    print(f"Error finding View Details buttons: {e}")
    driver.quit()
    exit()

# Ensure we have at least 6 buttons
if len(view_buttons) < 6:
    print(f"Warning: Only {len(view_buttons)} View Details buttons found. Expected at least 6.")

# Process the first 6 projects
for i in range(1, min(7, len(view_buttons) + 1)):
    print(f"\nProcessing project {i}...")
    try:
        # Refresh the main page for each iteration to avoid stale elements
        driver.get(url)
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Re-locate the View Details buttons
        view_buttons = driver.find_elements(By.XPATH, '//a[contains(text(),"View Details")]')
        print(f"[{i}] Found {len(view_buttons)} buttons")

        if i > len(view_buttons):
            print(f"Not enough buttons. Skipping project {i}.")
            continue

        # Click the "View Details" button
        button = view_buttons[i - 1]
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        driver.execute_script("arguments[0].click();", button)
        time.sleep(8)

        # Wait for the body to load
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        time.sleep(2)

        # Extract RERA Regd. No and Project Name
        try:
            rera_no = None
            try:
                rera_no = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "RERA") and contains(text(), "No")]/following-sibling::*'))).text
            except:
                try:
                    rera_no = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "RERA") and contains(text(), "No")]//parent::*/following-sibling::*'))).text
                except:
                    rera_no = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "RERA") and contains(text(), "No")]/..//following-sibling::*'))).text

            project_name = None
            try:
                project_name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Project Name")]/following-sibling::*'))).text
            except:
                try:
                    project_name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Project Name")]//parent::*/following-sibling::*'))).text
                except:
                    project_name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Project Name")]/..//following-sibling::*'))).text

            if not rera_no or not project_name:
                print(f"Could not find RERA Regd. No or Project Name for project {i}.")
                continue

        except Exception as e:
            print(f"Error extracting RERA Regd. No or Project Name for project {i}: {e}")
            continue

        # Click the Promoter Details tab
        try:
            promoter_tab = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "Promoter") and contains(text(), "Details")]')))
            driver.execute_script("arguments[0].click();", promoter_tab)
            time.sleep(6)
            # Wait for some content to load after clicking the tab
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Promoter") or contains(text(), "Company") or contains(text(), "Address") or contains(text(), "GST")]')))
            print(f"Successfully clicked Promoter Details tab for project {i}")
        except Exception as e:
            print(f"Error clicking Promoter Details tab for project {i}: {e}")
            continue

        # Extract Promoter Details with broader XPaths
        try:
            # Promoter Name
            promoter_name = None
            try:
                # Try a very generic XPath for any element containing "Name" and either "Promoter" or "Company"
                promoter_name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Name") and (contains(text(), "Promoter") or contains(text(), "Company"))]//following-sibling::*'))).text
            except:
                try:
                    promoter_name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Name") and (contains(text(), "Promoter") or contains(text(), "Company"))]//parent::*/following-sibling::*'))).text
                except:
                    try:
                        promoter_name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Name") and (contains(text(), "Promoter") or contains(text(), "Company"))]/..//following-sibling::*'))).text
                    except:
                        try:
                            # Try splitting the text if it's in the same element (e.g., <span>Promoter Name: ABC Corp</span>)
                            promoter_name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Name") and (contains(text(), "Promoter") or contains(text(), "Company"))]'))).text.split(":")[-1].strip()
                        except:
                            try:
                                # Try a table structure
                                promoter_name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Name") and (contains(text(), "Promoter") or contains(text(), "Company"))]/following-sibling::td'))).text
                            except:
                                try:
                                    # Try a very broad search for "Name"
                                    promoter_name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Name")]/following::*'))).text
                                except:
                                    print(f"Could not find Promoter Name for project {i}.")

            # Address
            address = None
            try:
                address = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Address")]/following-sibling::*'))).text
            except:
                try:
                    address = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Address")]//parent::*/following-sibling::*'))).text
                except:
                    try:
                        address = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Address")]/..//following-sibling::*'))).text
                    except:
                        try:
                            address = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Address")]/following::*'))).text
                        except:
                            try:
                                address = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Address")]/following-sibling::td'))).text
                            except:
                                print(f"Could not find Address for project {i}.")

            # GST No
            gst_no = None
            try:
                gst_no = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "GST")]/following-sibling::*'))).text
            except:
                try:
                    gst_no = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "GST")]//parent::*/following-sibling::*'))).text
                except:
                    try:
                        gst_no = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "GST")]/..//following-sibling::*'))).text
                    except:
                        try:
                            gst_no = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "GST")]/following::*'))).text
                        except:
                            try:
                                gst_no = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "GST")]/following-sibling::td'))).text
                            except:
                                print(f"Could not find GST No for project {i}.")

            # Fallback if not found
            promoter_name = promoter_name if promoter_name else "Not Found"
            address = address if address else "Not Found"
            gst_no = gst_no if gst_no else "Not Found"

            # Log the extracted values for debugging
            print(f"Extracted for project {i}: Promoter Name: {promoter_name}, Address: {address}, GST No: {gst_no}")

        except Exception as e:
            print(f"Error extracting Promoter Details for project {i}: {e}")
            promoter_name = "Not Found"
            address = "Not Found"
            gst_no = "Not Found"

        # Append the data
        projects_data.append({
            'RERA Regd. No': rera_no,
            'Project Name': project_name,
            'Promoter Name': promoter_name,
            'Promoter Address': address,
            'GST No': gst_no
        })
        print(f"Successfully scraped project {i}: {project_name}")

    except Exception as e:
        print(f"Error on project {i}: {e}")
        continue

# Close the driver
driver.quit()

# Save the data to CSV with error handling
if projects_data:
    df = pd.DataFrame(projects_data)
    try:
        df.to_csv("rera_projects.csv", index=False)
        print(f"✅ Data scraped and saved to rera_projects.csv. {len(projects_data)} projects saved.")
    except PermissionError as e:
        print(f"❌ PermissionError: Could not save to rera_projects.csv: {e}")
        print("Please ensure the file 'rera_projects.csv' is not open in another program (e.g., Excel) and that you have write permissions in the directory.")
        # Try saving to an alternative file name
        try:
            alternative_file = "rera_projects_backup.csv"
            df.to_csv(alternative_file, index=False)
            print(f"✅ Data scraped and saved to {alternative_file} as a fallback. {len(projects_data)} projects saved.")
        except Exception as e2:
            print(f"❌ Failed to save to alternative file {alternative_file}: {e2}")
            print("Please check your permissions and try again.")
else:
    print("❌ No data scraped. CSV file not created.")