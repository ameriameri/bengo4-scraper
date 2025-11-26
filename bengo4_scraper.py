import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

pref_code = os.getenv("PREF", "東京都")
print(f"ターゲット都道府県: {pref_code}")

def main():
    driver = webdriver.Chrome()

    try:
        driver.get("https://www.bengo4.com/search/")
        time.sleep(2)

        region_btn = driver.find_element(By.CSS_SELECTOR,
            "button.js-lawyerSearchPanel-modal-trigger[data-page='autonomyPrefecture']")
        print("地域から探すをクリックします")
        region_btn.click()
        time.sleep(1)
        
        target_pref_name = pref_code

        print(f"{target_pref_name} をクリックします")
    
        pref_btn = driver.find_element(
            By.XPATH,
            f"//button[contains(text(), '{target_pref_name}')]"
        )
        pref_btn.click()
        time.sleep(1)

    finally:
        driver.quit()

if __name__ == "__main__":
    print("スクリプト開始")
    main()
