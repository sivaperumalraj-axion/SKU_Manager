import os, re, json, time
import pandas as pd
from typing import Optional, Dict, Any, List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

# taskkill /F /IM chrome.exe

# =========================
# SETTINGS
# =========================
# PROFILE_DIR = r"./selenium_profile_bestbuy"
PROFILE_DIR = r"C:\Users\admin\Documents\selenium_profile_bestbuy"

INPUT_CSV   = r"./input - Sheet1.csv"
OUT_DIR     = r"./Bestbuy_Output_2"

PAGE_SIZE = 20
SORT = "BEST_REVIEW"  # or MOST_RECENT, MOST_HELPFUL, etc.
VARIANT = "A"

# polite delay (BestBuy can throttle)
SLEEP_BETWEEN_PAGES = 0.6


# =========================
# SELENIUM
# =========================
def start_driver() -> webdriver.Chrome:
    os.makedirs(PROFILE_DIR, exist_ok=True)
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument(fr"--user-data-dir={PROFILE_DIR}")
    opts.add_argument("--profile-directory=Default")

    # stability
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--remote-debugging-port=0")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    return driver


def read_json_from_current_page(driver: webdriver.Chrome) -> Dict[str, Any]:
    """
    BestBuy API pages usually render JSON inside <pre>.
    """
    try:
        pre = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "pre"))
        )
        txt = pre.text.strip()
    except Exception:
        txt = driver.find_element(By.TAG_NAME, "body").text.strip()

    # sometimes slow render
    if not txt or txt == "{}":
        time.sleep(1)
        try:
            pre = driver.find_element(By.TAG_NAME, "pre")
            txt = pre.text.strip()
        except Exception:
            txt = driver.find_element(By.TAG_NAME, "body").text.strip()

    return json.loads(txt)


# =========================
# SKU EXTRACTION (from product page)
# =========================
def extract_sku_from_url(url: str) -> Optional[str]:
    for rx in [
        re.compile(r"[?&]skuId=(\d{6,10})", re.I),
        re.compile(r"/(\d{6,10})\.p", re.I),
        re.compile(r"/sku/(\d{6,10})", re.I),
        re.compile(r"/(\d{6,10})(?:[/?#]|$)", re.I),
    ]:
        m = rx.search(url)
        if m:
            return m.group(1)
    return None


def extract_sku_from_html(html: str) -> Optional[str]:
    m = re.search(r'"skuId"\s*:\s*"?(\d{6,10})"?', html, flags=re.I)
    if m:
        return m.group(1)
    m = re.search(r'data-sku-id\s*=\s*"(\d{6,10})"', html, flags=re.I)
    if m:
        return m.group(1)
    return None


def resolve_sku_via_browser(driver: webdriver.Chrome, product_url: str) -> str:
    driver.get(product_url)

    print("Chrome opened product page. If any human-check appears, solve it now...")
    time.sleep(8)

    # from redirected URL
    sku = extract_sku_from_url(driver.current_url)
    if sku:
        return sku

    # from HTML
    html = driver.page_source or ""
    sku = extract_sku_from_html(html)
    if sku:
        return sku

    # retry once (SPA sometimes loads late)
    time.sleep(4)
    sku = extract_sku_from_url(driver.current_url) or extract_sku_from_html(driver.page_source or "")
    if sku:
        return sku

    raise RuntimeError("Could not resolve numeric SKU from product page.")


# =========================
# REVIEWS API
# =========================
def build_reviews_api_url(sku: str, page: int) -> str:
    return (
        "https://www.bestbuy.com/ugc/v2/reviews"
        f"?page={page}&pageSize={PAGE_SIZE}&sku={sku}&sort={SORT}&variant={VARIANT}"
    )


def get_total_pages_and_first_topics(driver: webdriver.Chrome, sku: str) -> (int, List[Dict[str, Any]], Dict[str, Any]):
    """
    Call page 1 and read:
      - totalPages (top-level)
      - topics list (reviews)
    """
    url = build_reviews_api_url(sku, 1)
    driver.get(url)
    data = read_json_from_current_page(driver)

    total_pages = int(data.get("totalPages", 1))
    topics = data.get("topics", []) or []

    return total_pages, topics, data


def scrape_all_pages(driver: webdriver.Chrome, sku: str) -> pd.DataFrame:
    total_pages, topics_page1, data_page1 = get_total_pages_and_first_topics(driver, sku)
    print(f"SKU {sku} -> totalPages = {total_pages}")

    all_topics = []
    if topics_page1:
        all_topics.extend(topics_page1)

    # loop remaining pages
    for page in range(2, total_pages + 1):
        url = build_reviews_api_url(sku, page)
        print(f"  Fetching page {page}/{total_pages}")
        driver.get(url)
        data = read_json_from_current_page(driver)

        topics = data.get("topics", []) or []
        if not topics:
            print(f"  No topics on page {page}. Stopping early.")
            break

        all_topics.extend(topics)
        time.sleep(SLEEP_BETWEEN_PAGES)

    df = pd.json_normalize(all_topics) if all_topics else pd.DataFrame()
    df["sku"] = sku
    df["sort"] = SORT
    df["pageSize"] = PAGE_SIZE
    return df


# =========================
# MAIN: FILE INPUT -> SAVE OUTPUT
# =========================
def safe_filename(name: str) -> str:
    # Windows-safe filename
    return re.sub(r'[\\/*?:"<>|]+', "_", name).strip()


def run_from_input_file(input_csv: str):
    os.makedirs(OUT_DIR, exist_ok=True)

    df_in = pd.read_csv(input_csv)

    # Expect columns: filename, url (or similar)
    # If your column names differ, adjust here:
    filename_col = "filename"
    url_col = "url"

    driver = start_driver()
    try:
        for idx, row in df_in.iterrows():
            filename = str(row[filename_col]).strip()
            product_url = str(row[url_col]).strip()

            if not filename or not product_url or product_url == "nan":
                print(f"\n[{idx}] Skipping empty row")
                continue

            print(f"\n[{idx}] Product: {product_url}")
            try:
                sku = resolve_sku_via_browser(driver, product_url)
                print(f"Resolved SKU: {sku}")

                reviews_df = scrape_all_pages(driver, sku)

                out_name = safe_filename(filename) + ".csv"
                out_path = os.path.join(OUT_DIR, out_name)
                reviews_df.to_csv(out_path, index=False)

                print(f"Saved: {out_path} ({len(reviews_df)} rows)")

            except Exception as e:
                print(f"❌ Failed row [{idx}] {product_url} -> {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    run_from_input_file(INPUT_CSV)
