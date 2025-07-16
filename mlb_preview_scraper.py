from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
from datetime import datetime
import psycopg2

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
def main():
    # Set up headless browser
    driver = get_driver()  
    wait = WebDriverWait(driver, 10)

    page_date = datetime.now().date()
    url = f"https://www.mlb.com/scores/{page_date}"
    driver.get(url)

    # Wait for all "Preview" buttons
    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[span[normalize-space()='Preview']]")))

    # Dismiss cookie overlay if present
    try:
        overlay = driver.find_element(By.CLASS_NAME, "onetrust-close-btn-container")
        overlay.click()
        time.sleep(1)
    except:
        pass

    # Grab all preview links by walking up to parent <a> of the <button>
    preview_links = []
    buttons = driver.find_elements(By.XPATH, "//button[span[normalize-space()='Preview']]")

    for btn in buttons:
        try:
            parent = btn.find_element(By.XPATH, "./ancestor::a")
            href = parent.get_attribute("href")
            if href:
                preview_links.append(href)
        except:
            continue

    print(f"🔗 Found {len(preview_links)} preview links.")

    results = []

    for i, link in enumerate(preview_links):
        try:
            driver.get(link)
            print(f"🔍 Visiting preview page {i + 1}: {link}")

            time.sleep(1)

            # Dismiss cookie banner again if it appears
            try:
                cookie_overlay = driver.find_element(By.XPATH, "//button[text()='OK']")
                driver.execute_script("arguments[0].click();", cookie_overlay)
                time.sleep(1)
                print("✅ Dismissed cookie banner")
            except:
                print("❌ No cookie banner found")

            wait.until(EC.presence_of_element_located((By.XPATH, "//main")))
            preview_text = driver.find_element(By.XPATH, "//main").text

            results.append({
                "game_index": i + 1,
                "game_date": str(page_date),
                "preview_text": preview_text
            })

        except TimeoutException:
            print(f"⚠️ Timeout on preview {i + 1}")
            continue
        except Exception as e:
            print(f"⚠️ Error on preview {i + 1}: {e}")
            continue

    driver.quit()

    # Save to file
    with open("mlb_previews.jsonl", "w", encoding="utf-8") as f:
        for row in results:
            json.dump(row, f)
            f.write("\n")

    print(f"\n✅ Saved {len(results)} game previews to mlb_previews.jsonl")

    # Insert into PostgreSQL
    try:
        conn = psycopg2.connect("postgresql://postgres:onfxNlZFioFScuucmNhZKHhzPggcMfvd@postgres.railway.internal:5432/railway")
        cur = conn.cursor()

        with open("mlb_previews.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                cur.execute("INSERT INTO json_mlb_previews(raw_json) VALUES (%s)", [json.dumps(json.loads(line))])

        conn.commit()
        cur.close()
        conn.close()
        print("📤 Uploaded to PostgreSQL on Railway")
    except Exception as e:
        print(f"❌ PostgreSQL upload failed: {e}")

if __name__ == "__main__":
    main()
