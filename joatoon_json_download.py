import os
import json
import time
import re
import requests
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 설정 변수 ---
INPUT_FILE = "webtoon_list.json"
DOWNLOAD_DIR = "downloaded_webtoons"
MAX_WORKERS = 8

stop_requested = False

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    return driver

def clean_filename(title):
    """줄바꿈 문자를 제거하고 윈도우 금지 문자를 정리합니다."""
    # 줄바꿈과 탭을 공백으로 치환
    title = re.sub(r'[\n\r\t]+', ' ', title)
    # 특수문자 제거
    title = re.sub(r'[\\/:*?"<>|]', '', title)
    # 중복 공백 정리 및 양끝 공백 제거
    return " ".join(title.split()).strip()

def download_image(img_url, folder_path, filename, referer):
    headers = {'User-Agent': 'Mozilla/5.0...', 'Referer': referer}
    try:
        resp = requests.get(img_url, headers=headers, timeout=30)
        resp.raise_for_status()
        with open(os.path.join(folder_path, filename), 'wb') as f:
            f.write(resp.content)
        return True
    except:
        return False

def run_downloader():
    global stop_requested
    if not os.path.exists(INPUT_FILE): return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        episodes = json.load(f)

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    driver = setup_driver()

    try:
        for idx, item in enumerate(episodes):
            if stop_requested: break

            ep_name = item['episode_name']
            ep_url = item['url']
            
            # 여기서 수정된 clean_filename이 호출되어 안전한 폴더명을 만듭니다.
            safe_folder_name = clean_filename(ep_name)
            print(f"[{idx+1}/{len(episodes)}] 다운로드 중: {safe_folder_name}")
            
            folder_path = os.path.join(DOWNLOAD_DIR, safe_folder_name)
            os.makedirs(folder_path, exist_ok=True)

            driver.get(ep_url)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            img_elements = driver.find_elements(By.CSS_SELECTOR, "img[data-src]")
            img_urls = [img.get_attribute('data-src') for img in img_elements if img.get_attribute('data-src')]

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                for i, img_url in enumerate(img_urls):
                    ext_match = re.search(r'\.(jpg|jpeg|png|webp|gif)', img_url.lower())
                    ext = ext_match.group(1) if ext_match else "jpg"
                    executor.submit(download_image, img_url, folder_path, f"{i+1:03d}.{ext}", ep_url)

    finally:
        driver.quit()
        print("\n[알림] 작업이 종료되었습니다.")

if __name__ == "__main__":
    run_downloader()
