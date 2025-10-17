import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from concurrent.futures import ThreadPoolExecutor, as_completed 

# --- 설정 변수 ---
# ⚠️ BASE_URL을 여러 개의 웹툰 목록 URL을 포함하는 '리스트'로 변경합니다.
BASE_URLS = [
    "https://joatoon69.com/toon/w/2765?cso=desc",   # 아카데미 야겜에 빙의했다
    "https://joatoon69.com/toon/w/3398?cso=desc",   # 내 맘대로 이세계 최면
    "https://joatoon69.com/toon/w/3082?cso=desc",   # 히어로 매니저
    "https://joatoon69.com/toon/w/6083?cso=desc",   # 릴리스 코드
    "https://joatoon69.com/toon/w/3367?cso=desc",   # 곤란해요, 여신님!
    "https://joatoon69.com/toon/w/6111?cso=desc",   # 섹스레슨
    "https://joatoon69.com/toon/w/3276?cso=desc",   # 조여주세요
    "https://joatoon69.com/toon/w/5006?cso=desc",   # 나의 아저씨
    "https://joatoon69.com/toon/w/3599?cso=desc",   # 서큐버스 시스템
    "https://joatoon69.com/toon/w/3191?cso=desc",   # 상아
    "https://joatoon69.com/toon/w/3066?cso=desc",   # 퇴근, 할 거야?
    "https://joatoon69.com/toon/w/5069?cso=desc",   # 반품여친
    "https://joatoon69.com/toon/w/3059?cso=desc"    # 키다리 아가씨
]
# 다운로드 파일을 저장할 상위 폴더 이름
DOWNLOAD_DIR = "downloaded" 
# 병렬 다운로드에 사용할 최대 스레드(워커) 수
MAX_WORKERS = 10 

# (setup_driver, clean_filename, download_file 함수는 이전과 동일하게 유지됩니다.)
def setup_driver():
    """Chrome WebDriver를 설정하고 초기화합니다."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("--window-size=1920,1080") 
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver

def clean_filename(title):
    """폴더 및 파일 이름으로 사용할 수 없는 문자를 정리합니다."""
    title = re.sub(r'[\\/:*?"<>|]', '', title)
    return title.strip()

def download_file(img_url, folder_path, filename, referer_url):
    """이미지 파일을 다운로드하고 지정된 폴더에 저장합니다."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': referer_url 
        }
        response = requests.get(img_url, headers=headers, stream=True, timeout=30) 
        response.raise_for_status() 

        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return f"다운로드 성공: {filename}"
    except requests.exceptions.RequestException as e:
        return f"다운로드 실패: {filename} (URL: {img_url}, 오류: {e})"

# --------------------------------------------------------------------------------
# 핵심 수정 부분: BASE_URLS 리스트를 순회하도록 변경
# --------------------------------------------------------------------------------
def scrape_webtoon():
    """BASE_URLS 리스트에 있는 모든 웹툰 목록을 순회하며 에피소드와 이미지를 처리합니다."""
    driver = setup_driver()
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    try:
        # BASE_URLS 리스트를 순회합니다.
        for base_url in BASE_URLS:
            print(f"\n\n=======================================================")
            print(f"새 웹툰 목록 처리 시작: {base_url}")
            print(f"=======================================================")
            
            try:
                # 1. 웹툰 목록 페이지 접속
                driver.get(base_url)
                
                # 2. 에피소드 URL 수집
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/c/']"))
                )
                
                episode_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/c/']")
                episode_links = [(elem.get_attribute('href'), elem.text.strip()) for elem in episode_elements if elem.get_attribute('href') and '/c/' in elem.get_attribute('href')]
                
                if not episode_links:
                    print("에피소드 링크를 찾을 수 없습니다. 다음 URL로 넘어갑니다.")
                    continue

                print(f"총 {len(episode_links)}개의 에피소드 링크를 찾았습니다.")

                # 3. 각 에피소드 처리 (기존 로직 유지)
                for ep_url, ep_title_text in episode_links:
                    if not ep_url or not ep_url.startswith('http'):
                        continue

                    print(f"\n--- 에피소드 처리: {ep_title_text} ---")
                    
                    try:
                        # 3-1. 에피소드 페이지 접속
                        driver.get(ep_url)
                        
                        # 3-2. 제목 추출 및 폴더 생성
                        ep_title_element = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "h2.text-xl.tracking-tighter.text-gray-800"))
                        )
                        folder_name = clean_filename(ep_title_element.text.strip())
                        if not folder_name:
                            folder_name = clean_filename(ep_title_text) 
                            
                        ep_folder_path = os.path.join(DOWNLOAD_DIR, folder_name)
                        os.makedirs(ep_folder_path, exist_ok=True)
                        print(f"   -> 폴더 생성: {ep_folder_path}")

                        # 3-3. 이미지 로딩을 위한 페이지 스크롤
                        last_height = driver.execute_script("return document.body.scrollHeight")
                        print("   -> 모든 이미지 로딩을 위해 페이지 스크롤 중...")
                        while True:
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(1.5) 
                            new_height = driver.execute_script("return document.body.scrollHeight")
                            if new_height == last_height:
                                break 
                            last_height = new_height
                        
                        # 3-4. 이미지 URL 추출
                        WebDriverWait(driver, 30).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.w-full.h-auto.undraggable.unselectable.lazy.loaded"))
                        )
                        image_elements = driver.find_elements(By.CSS_SELECTOR, "img.w-full.h-auto.undraggable.unselectable.lazy.loaded")
                        image_urls = []

                        for img_elem in image_elements:
                            final_url = img_elem.get_attribute('src') or img_elem.get_attribute('data-src')
                            if final_url and final_url.startswith('http') and final_url not in image_urls:
                                image_urls.append(final_url)
                        
                        if not image_urls:
                            print("   -> 오류: 에피소드에서 이미지 URL을 찾을 수 없습니다.")
                            continue
                            
                        print(f"   -> 총 {len(image_urls)}개의 이미지 URL 추출 완료. 병렬 다운로드를 시작합니다 (워커: {MAX_WORKERS}).")

                        # 3-5. ThreadPoolExecutor를 사용한 이미지 병렬 다운로드
                        futures = []
                        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                            for i, img_url in enumerate(image_urls):
                                file_extension = img_url.split('.')[-1].split('?')[0]
                                if not file_extension or len(file_extension) > 4: 
                                     file_extension = 'jpg' 
                                filename = f"{i + 1:03d}.{file_extension}" 
                                
                                future = executor.submit(download_file, img_url, ep_folder_path, filename, ep_url)
                                futures.append(future)

                            # 모든 작업 결과를 출력 (순서 보장 안됨)
                            for future in as_completed(futures):
                                print(f"     [>] {future.result()}")
                        
                        print(f"\n   -> {folder_name} 에피소드 병렬 다운로드 완료. ({len(image_urls)}개 파일)")

                    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
                        print(f"에피소드 '{ep_title_text}' 처리 중 오류 발생: {e}")
                
            except Exception as e:
                print(f"웹툰 목록 '{base_url}' 처리 중 치명적인 오류 발생: {e}")
        
    except Exception as e:
        print(f"스크립트 실행 중 전역 오류 발생: {e}")
        
    finally:
        print("\n=======================================================")
        print("4. WebDriver 종료. 모든 스크래핑 완료.")
        driver.quit()

if __name__ == "__main__":
    scrape_webtoon()
