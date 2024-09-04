import concurrent.futures
import re
import os
import time
import winsound  # 알림 소리를 위한 모듈
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor
import requests

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
def optimized_download_images(page_number):
    # 이미지가 로드되기를 기다리는 시간 최적화 (현재는 10초 대기)
    images = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#toon_img img')))
    
    try:
        comic_name_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.toon-title')))
        comic_name = comic_name_element.text.strip()
        if not comic_name:
            raise ValueError("제목이 비어 있습니다.")
        comic_name = sanitize_filename(comic_name)
    except Exception as e:
        print(f"만화 제목을 가져오는 중 오류 발생: {e}")
        comic_name = f"default_comic_name_page_{page_number}"  # 페이지 번호 추가하여 중복 방지

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
        concurrent.futures.wait(futures, timeout=30)  # 최대 30초까지 기다리기
    
    return comic_dir, comic_name

# 다음 페이지로 이동하는 함수
def click_next_page():
    try:
        next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn-resource.btn-next.at-tip')))
        ActionChains(driver).move_to_element(next_button).click().perform()
        print("다음 페이지로 이동합니다.")
    except Exception as e:
        print("더 이상 다음 버튼이 없습니다. 종료합니다.")
        print(f"오류: {str(e)}")
        return False  # 더 이상 페이지를 이동할 수 없음
    return True

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

# 주요 실행부
if __name__ == "__main__":
    # 크롬 드라이버 옵션 설정 (헤드리스 모드)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 창 숨김
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)  # 숨김 모드로 실행
    wait = WebDriverWait(driver, 10)
    download_dir = r"C:\Users\jjc\Downloads\pythonWork\downloaded"  # 다운로드 폴더 경로
    
    url_list = []
    
    while True:
        user_input = input("다운로드 시작할 toonkor URL을 리스트에 적재합니다. 'download start'를 입력하면 다운로드가 시작됩니다. ")
        if user_input.lower() == 'download start':
            break
        elif user_input.strip():
            url_list.append(user_input.strip())
    
    for user_input in url_list:
        driver.get(user_input)

        folder_paths = []
        first_comic_name = None
        page_number = 1

        while True:
            try:
                comic_dir, comic_name = optimized_download_images(page_number)
                folder_paths.append(comic_dir)

                if first_comic_name is None:
                    first_comic_name = comic_name

                if not click_next_page():
                    print("현재 URL의 모든 페이지 다운로드가 완료되었습니다.")
                    break

                page_number += 1
                time.sleep(1)
            except Exception as e:
                print("오류 발생, 종료합니다.")
                print(f"오류: {str(e)}")
                break

    # 작업 완료 시 알림 소리
    winsound.Beep(1000, 500)  # 1000 Hz 주파수로 0.5초 동안 소리 재생
    
    print("모든 다운로드가 완료되었습니다.")
    driver.quit()
    
    #시스템 종료
    shutdown_system()
