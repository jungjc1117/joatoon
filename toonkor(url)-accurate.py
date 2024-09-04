import os
import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, wait as futures_wait  # 'wait'를 'futures_wait'로 가져오기
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Selenium WebDriver 설정
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--ignore-certificate-errors')

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# 파일명을 정리하는 함수
def sanitize_filename(filename):
    """파일명에서 허용되지 않는 문자들을 제거합니다."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

# 이미지를 다운로드하는 함수
def download_image(session, img_url, comic_dir, idx):
    try:
        response = session.get(img_url)
        if response.status_code == 200:
            image_path = os.path.join(comic_dir, f"image_{idx + 1}.jpg")
            with open(image_path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded: {image_path}")
    except Exception as e:
        print(f"이미지 다운로드 중 오류 발생: {e}")

# 이미지를 최적화하여 다운로드하는 함수
def optimized_download_images(page_number, download_dir):
    # 이미지가 로드되기를 기다리는 시간 최적화 (현재는 10초 대기)
    images = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#toon_img img')))
    
    try:
        # 만화 제목을 가져와서 파일명에 사용할 수 있도록 정리
        comic_name_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.toon-title')))
        comic_name = comic_name_element.text.strip()
        if not comic_name:
            raise ValueError("제목이 비어 있습니다.")
        comic_name = sanitize_filename(comic_name)
    except Exception as e:
        print(f"만화 제목을 가져오는 중 오류 발생: {e}")
        comic_name = f"default_comic_name_page_{page_number}"  # 페이지 번호 추가하여 중복 방지

    # 다운로드할 디렉토리 생성
    comic_dir = os.path.join(download_dir, comic_name)
    if not os.path.exists(comic_dir):
        os.makedirs(comic_dir)

    # 세션 생성 및 이미지 병렬 다운로드
    session = requests.Session()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for idx, img in enumerate(images):
            img_url = img.get_attribute('src')
            if img_url:
                futures.append(executor.submit(download_image, session, img_url, comic_dir, idx))
        
        # 다운로드가 완료될 때까지 기다리지 않고 페이지를 넘기는 작업을 진행
        futures_wait(futures, timeout=30)  # 'futures_wait' 사용하여 최대 30초까지 기다리기

    return comic_dir, comic_name

# 에피소드 인덱스를 가져오는 함수
def get_episode_index(driver):
    try:
        # 'episode__index' 클래스를 가진 모든 요소를 선택
        episode_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'episode__index')))
        
        # 'data-role' 속성값을 리스트로 저장
        base_url = "https://toonkor433.com"
        episode_index_list = [
            base_url + role if role else None 
            for role in (element.get_attribute('data-role') for element in episode_elements)
        ]
        
        # None 값 제거
        episode_index_list = [url for url in episode_index_list if url is not None]
        
        return episode_index_list
    except Exception as e:
        print(f"에피소드 인덱스를 가져오는 중 오류 발생: {e}")
        return []

# URL 리스트에 있는 각 페이지에 들러 이미지를 다운로드하는 메인 함수
def download_comics_from_urls(url_list, download_dir):
    for idx, url in enumerate(url_list):
        try:
            # URL로 이동
            driver.get(url)
            print(f"Accessed URL: {url}")
            
            # 이미지 다운로드 함수 호출
            optimized_download_images(idx + 1, download_dir)
            
            # 각 페이지마다 10초 대기 (옵션)
            time.sleep(10)
        except Exception as e:
            print(f"페이지 접속 중 오류 발생: {e}")

# 시스템 종료
def shutdown_system():
    try:
        if platform.system() == "Windows":
            os.system("shutdown /s /t 1")  # Windows용 시스템 종료 명령어
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            os.system("sudo shutdown -h now")  # Linux 및 macOS용 시스템 종료 명령어
        else:
            print("지원하지 않는 운영 체제입니다.")
    except Exception as e:
        print(f"시스템 종료 중 오류 발생: {e}")
        
# 사용 예시
if __name__ == "__main__":
    # 다수의 URL에서 에피소드 인덱스 가져오기
    urls_to_check = [
        "https://toonkor433.com/%EB%B0%98%ED%92%88%EC%97%AC%EC%B9%9C",
        "https://toonkor433.com/%ED%87%B4%EA%B7%BC-%ED%95%A0-%EA%B1%B0%EC%95%BC",
        "https://toonkor433.com/%EC%B9%9C%EA%B5%AC%EB%A7%90%EA%B3%A0"
    ]
    
    # 모든 에피소드 인덱스 결합
    all_episode_index_list = []
    for url in urls_to_check:
        driver.get(url)
        episode_index_list = get_episode_index(driver)
        all_episode_index_list.extend(episode_index_list)
    
    print("All Episode Index List with Full URLs:", all_episode_index_list)
    
    # 이미지 다운로드 디렉토리 설정
    download_dir = "downloaded"
    
    # URL 리스트에 있는 각 페이지에 들러서 이미지 다운로드
    download_comics_from_urls(all_episode_index_list, download_dir)
    
    # 드라이버 종료
    driver.quit()

    #시스템 종료
    shutdown_system()
