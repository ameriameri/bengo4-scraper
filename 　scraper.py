import os
import time
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#環境変数

PREF = os.getenv("PREF","東京都") #都道府県名
CITY = os.getenv("CITY","東京都すべてを選択") #市区町村画面でクリックするラベルの文言
FIELD = os.getenv("FIELD","指定しない、またはわからない") # 相談内容画面で選択するラジオボタンの文言
MAX_LAWYERS = int(os.getenv("MAX_LAWYERS","1000")) #最大取得人数（安全のため上限）
MAX_PAGES = int(os.getenv("MAX_PAGES","999")) #最大取得ページ数（全部なら大きな値に）

print(f"ターゲット都道府県:{PREF}")
print(f"市区町村選択:{CITY}")
print(f"相談内容:{FIELD}")
print(f"取得する弁護士の最大人数:{MAX_LAWYERS}")
print(f"取得するページの最大数:{MAX_PAGES}")

# ==== 共通ヘルパー ====

def wait(driver, sec=10):
    return WebDriverWait(driver, sec)

def click_css(driver, selector):
    el = wait(driver).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    driver.execute_script("arguments[0].click();",el)

def click_xpath(driver,xpath):
    el = wait(driver).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    driver.execute_script("arguments[0].click();", el)

def click_label_input(driver, label_text, input_type):
    """ラベルのテキストで label を探し、中の input をクリック"""
    xpath = (
        "//label[contains(@class,'uniq-lawyer-search-panel__list-label')]"
        f"[contains(., '{label_text}')]//input[@type='{input_type}']"
    )
    click_xpath(driver, xpath)

# ==== 画面遷移 ====


def click_region(driver):
  """地域から探す　→　都道府県を選択"""
  driver.get("https://www.bengo4.com/search/")

  print("地域から探すをクリックします")

  #「地域から探す」ボタン
  click_css(
        driver,
        "button.js-lawyerSearchPanel-modal-trigger[data-page='autonomyPrefecture']",
  )
    

  #「都道府県」ボタン
  print(f"{PREF}をクリックします")
  click_xpath(driver, f"//button[contains(text(), '{PREF}')]")

def select_city(driver):
    """市区町村画面でチェックを付ける"""
    print(f"市区町村:{CITY}にチェックを付けます")
    click_label_input(driver, CITY, "checkbox")

def go_to_field_page(driver):
    """「相談内容を選ぶ」ボタンを押す"""
    print("相談内容を選ぶボタンをクリックします")
    click_css(driver, "button.uniq-lawyer-search-panel__next-button")

def select_field(driver):
    """相談内容画面でラジオボタンを選択"""
    print(f"相談内容: {FIELD} を選択")
    click_label_input(driver, FIELD, "radio")

def click_search(driver):
    """「検索」ボタンを押す"""
    print("検索ボタンをクリックします")
    click_css(driver, "a.uniq-lawyer-search-panel__submit-button")

# ==== データ取得 ====

def collect_lawyer_profiles_with_pagination(driver,
                                            max_lawyers=1000,
                                            max_pages=999):
    """
    検索結果をページ送りしながら、
    弁護士プロフィールを順番に開いて名前を取得する。
    """
    lawyer_list = []
    page = 1

    while page <= max_pages and len(lawyer_list) < max_lawyers:
        print(f"==={page} ページ目の情報を取得します ===")

        #ページ読み込み待ち（検索結果本体がある要素を待つのが理想）
        wait(driver).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(1) #レイアウトの安定待ち（必要に応じて調整）

        # このページの弁護士リンクを順番に処理
        idx_on_page = 0
        while len(lawyer_list) < max_lawyers:
            #※ 戻るたびに要素が再生成されるので、その都度取り直す
            lawyer_links = driver.find_elements(
                By.XPATH,
                #「○○弁護士の詳細情報を見る」のボタンに合わせて調整する
                "//a[contains(@href, '/lawyer/') and contains(., '弁護士の詳細情報を見る')]",
            )

            if idx_on_page >= len(lawyer_links):
                break # このページの弁護士は処理完了

            target_link = lawyer_links[idx_on_page]
            idx_global = len(lawyer_list) + 1
            print(f"{idx_global}人目(ページ内{idx_on_page + 1}人目)をクリック")

            driver.execute_script("arguments[0].click();", target_link)

            wait(driver).until(
                EC.presence_of_element_located(
                      (By.CSS_SELECTOR,".p-lawyer-profile-header__name-wrap")
                )
            )

            try:
                kana = driver.find_element(
                    By.CSS_SELECTOR, ".p-lawyer-profile-header__kana"
                ).text.strip()
                name_full = driver.find_element(
                    By.CSS_SELECTOR,".p-lawyer-profile-header__name"
                ).text.strip()
            except Exception as e:
                print(f"名前取得に失敗: {e}")
                kana, name_full = "",""

            print(f"取得: {kana} / {name_full}")
            lawyer_list.append(
                {"index": idx_global, "kana": kana, "name": name_full}
            )

            driver.back()
            wait(driver).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(1)
            idx_on_page += 1

        if len(lawyer_list) >= max_lawyers:
            break

        #次ページへ
        try:
            next_btn = driver.find_element(
                By.XPATH,
                "//a[contains(@class,'c-pagination__item-next') or .='›' or .='>']",
            )
            if "is-disabled" in next_btn.get_attribute("class"):
                print("次ページボタン無効のため終了")
                break

            print("次ページへ")
            driver.execute_script("arguments[0].click();", next_btn)
            page += 1
        except Exception:
            print("次ページボタンが見つからないため終了")
            break

    return lawyer_list

def export_to_csv(lawyer_list, filename="lawyers.csv"):
    if not lawyer_list:
        print("出力データがありません")
        return

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["index","kana","name"])
        writer.writeheader()
        writer.writerows(lawyer_list)

    print(f"CSV 出力完了:{filename}")

# ==== エントリーポイント ====
            
def main():
    print("スクリプト開始")

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    try:
        click_region(driver)
        select_city(driver)
        go_to_field_page(driver)
        select_field(driver)
        click_search(driver)

        lawyers = collect_lawyer_profiles_with_pagination(
            driver,
            max_lawyers=MAX_LAWYERS,
            max_pages=MAX_PAGES,
        )

        print("=== 取得結果 ===")
        for l in lawyers:
            print(f"{l['index']}人目: {l['kana']} / {l['name']}")

        export_to_csv(lawyers)
    finally:
        driver.quit()

if __name__=="__main__":
    main()


















