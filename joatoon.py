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
    "https://joatoon69.com/toon/w/8784?cso=desc",    # 신입사원 김철수

    "https://joatoon69.com/toon/w/7342?cso=desc",    # 사신소년
    "https://joatoon69.com/toon/w/1948?cso=desc",    # 나쁜사람
    "https://joatoon69.com/toon/w/12163?cso=desc",    # 쓰레기의 사정
    "https://joatoon69.com/toon/w/2263?cso=desc",    # 왕따가 격투기를 너무 잘함
    "https://joatoon69.com/toon/w/1611?cso=desc",    # 절대역
    "https://joatoon69.com/toon/w/12711?cso=desc",    # 이직로그
]
# 다운로드 파일을 저장할 상위 폴더 이름
DOWNLOAD_DIR = "downloaded" 
# 병렬 다운로드에 사용할 최대 스레드(워커) 수
MAX_WORKERS = 10 

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
# 핵심 구현: 링크 수집(Phase 1) 완료 후 일괄 다운로드(Phase 2)
# --------------------------------------------------------------------------------
def scrape_webtoon():
    """
    BASE_URLS 리스트에서 모든 에피소드 링크를 수집(Phase 1)한 후, 
    수집된 링크들을 순서대로 순회하며 이미지 다운로드(Phase 2)를 진행합니다.
    """
    driver = setup_driver()
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    all_episode_links = [] # 수집된 모든 에피소드 링크를 저장할 통합 리스트

    try:
        # =========================================================================
        # [ Phase 1: 링크 수집 ] - 모든 BASE_URLS를 순회하며 링크를 통합 리스트에 저장
        # =========================================================================
        print("*************************************************************************")
        print(" Phase 1: 모든 웹툰 목록에서 에피소드 링크 수집 시작 (다운로드는 아직 시작하지 않습니다)")
        print("*************************************************************************")
        
        # 💡 이 루프는 모든 BASE_URLS의 링크를 all_episode_links에 모으는 데 사용됩니다.
        for base_url in BASE_URLS:
            print(f"\n[수집 진행] 웹툰 목록 페이지 접속: {base_url}")
            
            try:
                driver.get(base_url)
                
                # 스크롤 루프: 모든 에피소드가 로드될 때까지 스크롤
                print(" -> 모든 에피소드 로딩을 위해 목록 페이지 스크롤 중...")
                last_height = driver.execute_script("return document.body.scrollHeight")
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5) # 페이지 로딩 대기 시간
                    
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    
                    if new_height == last_height:
                        print(" -> 페이지 끝 도달 완료.")
                        break 
                    last_height = new_height
                
                # 에피소드 URL 수집 (a[href*='/c/'] 요소 찾기)
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/c/']"))
                )
                
                episode_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/c/']")
                
                # 추출 및 통합 리스트에 추가
                new_links = [(elem.get_attribute('href'), elem.text.strip()) 
                                 for elem in episode_elements 
                                 if elem.get_attribute('href') and '/c/' in elem.get_attribute('href') and elem.text.strip()]
                
                all_episode_links.extend(new_links)
                
                print(f" -> '{base_url}'에서 {len(new_links)}개의 링크 수집 완료. (누적 링크 수: {len(all_episode_links)}개)")

            except Exception as e:
                print(f"오류: 웹툰 목록 '{base_url}' 처리 중 치명적인 오류 발생. 이 URL은 건너뛰고 다음 URL 수집을 진행합니다. 오류: {e}")
                continue 

        print("\n\n*************************************************************************")
        print(f" [SUCCESS] Phase 1 완료: 총 {len(all_episode_links)}개의 에피소드 링크 수집.")
        print("*************************************************************************")

        # --- 사용자 요청: 수집된 모든 링크를 출력 ---
        print("\n[수집된 통합 에피소드 리스트 (다운로드 순서)]")
        if all_episode_links:
            for i, (url, title) in enumerate(all_episode_links):
                # print(f"   {i + 1:03d}. 제목: {title}, URL: {url}")
                print(f"{url}")
        else:
            print("   (리스트가 비어 있습니다.)")
        print("-------------------------------------------------------------------------")
        # -----------------------------------------------

        # =========================================================================
        # [ Phase 2: 다운로드 실행 ] - 수집된 통합 리스트 순회하며 이미지 다운로드
        # =========================================================================
        
        if not all_episode_links:
            print("경고: 수집된 에피소드 링크가 없어 다운로드를 시작할 수 없습니다.")
            return

        print("\n--- Phase 2: 수집된 통합 링크 리스트를 순서대로 다운로드 시작 ---")
        
        # 💡 이 루프는 수집된 전체 링크에 대해 순차적으로 다운로드를 진행합니다.
        for index, (ep_url, ep_title_text) in enumerate(all_episode_links):
            print(f"\n--- 에피소드 처리 ({index + 1}/{len(all_episode_links)}): {ep_title_text} ({ep_url}) ---")
            
            if not ep_url or not ep_url.startswith('http'):
                print(" -> 경고: 유효하지 않은 에피소드 URL입니다. 건너뜁니다.")
                continue

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
                print(f"   -> 폴더 생성: {ep_folder_path}")

                # 3-3. 이미지 로딩을 위한 페이지 스크롤 (에피소드 내용 스크롤)
                last_height = driver.execute_script("return document.body.scrollHeight")
                print("   -> 모든 이미지 로딩을 위해 에피소드 페이지 스크롤 중...")
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5) 
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break 
                    last_height = new_height
                
                # 3-4. 이미지 URL 추출 및 다운로드
                WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img[data-src]"))
                )

                image_elements = driver.find_elements(By.CSS_SELECTOR, "img[data-src]")

                image_urls = []
                for img_elem in image_elements:
                    final_url = img_elem.get_attribute('data-src') or img_elem.get_attribute('src')
                    if final_url and final_url.startswith('http') and final_url not in image_urls:
                        image_urls.append(final_url)
                
                if not image_urls:
                    print("   -> 오류: 에피소드에서 이미지 URL을 찾을 수 없습니다. 건너뜁니다.")
                    continue
                    
                print(f"   -> 총 {len(image_urls)}개의 이미지 URL 추출 완료. 병렬 다운로드를 시작합니다 (워커: {MAX_WORKERS}).")

                # 3-5. ThreadPoolExecutor를 사용한 이미지 병렬 다운로드
                futures = []
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    for i, img_url in enumerate(image_urls):
                        url_path = img_url.split('?')[0]
                        file_extension = url_path.split('.')[-1]
                        
                        valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
                        if not file_extension or file_extension.lower() not in valid_extensions:
                            file_extension = 'jpg' 
                            
                        filename = f"{i + 1:03d}.{file_extension}" 
                        
                        future = executor.submit(download_file, img_url, ep_folder_path, filename, ep_url)
                        futures.append(future)

                    for future in as_completed(futures):
                        print(f"     [>] {future.result()}")
                
                print(f"\n   -> {folder_name} 에피소드 병렬 다운로드 완료. ({len(image_urls)}개 파일)")

            except (TimeoutException, NoSuchElementException, WebDriverException) as e:
                print(f"치명적 오류: 에피소드 '{ep_title_text}' 처리 중 오류 발생: {e}. 이 에피소드는 건너뜁니다.")
                continue # 다음 에피소드로 이동
            
    except Exception as e:
        print(f"스크립트 실행 중 전역 오류 발생: {e}")
        
    finally:
        print("\n=======================================================")
        print("4. WebDriver 종료. 모든 스크래핑 완료.")
        driver.quit()

if __name__ == "__main__":
    scrape_webtoon()
    # os.system("shutdown -s -t 5")
