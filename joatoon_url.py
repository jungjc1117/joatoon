import os
import re
import time
import json
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 설정 변수 ---
BASE_URLS = [
    "https://joatoon69.com/toon/w/1948?cso=desc",    # 나쁜사람
    "https://joatoon69.com/toon/w/12163?cso=desc",   # 쓰레기의 사정
    "https://joatoon69.com/toon/w/2263?cso=desc",    # 왕따가 격투기를 너무 잘함
    "https://joatoon69.com/toon/w/1611?cso=desc",    # 절대역
    "https://joatoon69.com/toon/w/12711?cso=desc",   # 이직로그
]
OUTPUT_FILE = "webtoon_list.json"

# --- 전역 변수 (중단 플래그) ---
stop_requested = False

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver

def scrape_to_json():
    global stop_requested
    driver = setup_driver()
    
    # 최종 데이터를 저장할 리스트
    final_data = []

    try:
        for index, base_url in enumerate(BASE_URLS):
            print(f"\n[{index + 1}/{len(BASE_URLS)}] 목록 수집 중: {base_url}")
            
            try:
                driver.get(base_url)
                
                # 모든 에피소드 로딩을 위한 스크롤
                last_height = driver.execute_script("return document.body.scrollHeight")
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                # 에피소드 요소 추출
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/c/']"))
                )
                elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/c/']")

                # 요청하신 양식대로 데이터 구성
                for elem in elements:
                    title = elem.text.strip()
                    url = elem.get_attribute('href')
                    
                    if title and url:
                        final_data.append({
                            "episode_name": title,
                            "url": url
                        })
                
                print(f" -> 현재까지 총 {len(final_data)}개의 에피소드 수집됨.")

            except Exception as e:
                print(f" -> 오류 발생 ({base_url}): {e}")
                continue

            # 작품 하나가 끝날 때마다 중단 플래그 확인
            if stop_requested:
                print("\n[!] 중단 요청에 따라 수집을 종료하고 파일 저장을 시작합니다.")
                break

    finally:
        # JSON 파일 저장
        if final_data:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            print(f"\n[성공] 총 {len(final_data)}개의 목록이 '{OUTPUT_FILE}'에 저장되었습니다.")
        else:
            print("\n[알림] 수집된 데이터가 없어 파일이 생성되지 않았습니다.")
            
        driver.quit()

if __name__ == "__main__":
    scrape_to_json()
