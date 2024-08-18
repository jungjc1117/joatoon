from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import requests
import time
import platform
import zipfile


        
def downloadimages():
    # geckodriver의 경로를 명시적으로 지정
    gecko_driver_path = r"C:\Users\jjc\Downloads\pythonWork\geckodriver32.exe"

    # Firefox 실행 파일의 경로 지정
    firefox_binary_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"

    # Firefox 옵션 설정
    options = Options()
    options.binary_location = firefox_binary_path

    # Service 객체 생성
    service = Service(executable_path=gecko_driver_path)

    # Firefox WebDriver 시작
    driver = webdriver.Firefox(service=service, options=options)

    # 순환할 숫자 범위 설정 (예: 1부터 10까지)
    for i in range(1, 81):  # 예: 1부터 10까지
        # 순환할 URL 설정
        url = f"https://toonkor428.com/%EC%8B%9C%EC%B2%B4%EA%B8%B0%EC%82%AC_%EA%B5%B0%ED%84%B0_{i}%ED%99%94.html"
        print(f"Loading URL: {url}")
        driver.get(url)
        
        # 페이지가 완전히 로드될 때까지 대기
        try:
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#toon_img"))
            )
        except Exception as e:
            print(f"Error while waiting for page to load (URL: {url}): {e}")
            continue

        # 이미지가 포함된 요소 선택 (예: #toon_img 아래의 모든 img 태그)
        images = driver.find_elements(By.CSS_SELECTOR, "#toon_img img")

        # 이미지를 저장할 디렉토리 생성
        download_dir = f"{i}"
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # 이미지 다운로드
        for idx, img in enumerate(images):
            img_url = img.get_attribute("src")
            if img_url:  # URL이 비어 있지 않은지 확인
                try:
                    img_data = requests.get(img_url).content
                    img_name = os.path.join(download_dir, f"image_{idx+1}.jpg")
                    
                    with open(img_name, 'wb') as handler:
                        handler.write(img_data)
                        print(f"Downloaded: {img_name}")
                except Exception as e:
                    print(f"Error downloading image {img_url}: {e}")
                    
        # 다음 페이지로 넘어가기 전에 잠시 대기
        time.sleep(2)

    # 작업이 끝난 후 브라우저를 닫음
    driver.quit()
    
def zip_folders(folder_paths, zip_name):
    """
    주어진 폴더들을 하나의 ZIP 파일로 압축합니다.

    :param folder_paths: 압축할 폴더들의 경로 리스트 (예: ['folder1', 'folder2', ...])
    :param zip_name: 생성할 ZIP 파일의 이름 (확장자 제외, 예: 'archive_name')
    """
    # 지정된 이름으로 ZIP 파일을 만듭니다.
    zip_path = f"{zip_name}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for folder in folder_paths:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    # 폴더 구조를 유지한 채로 파일을 추가합니다.
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.join(folder, '..'))
                    zipf.write(file_path, arcname)
    
    print(f"'{zip_path}' 파일이 생성되었습니다.")
    
def shutdown_system():
    """
    시스템을 종료합니다.
    """
    try:
        if platform.system() == "Windows":
            os.system("shutdown /s /t 1")
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            os.system("sudo shutdown -h now")
        else:
            print("지원하지 않는 운영 체제입니다.")
    except Exception as e:
        print(f"시스템 종료 중 오류 발생: {e}")
        

if __name__ == "__main__":
    downloadimages()
    
    # 압축할 폴더 경로 리스트
    folder_paths = [str(i) for i in range(1, 80)]
    # 생성할 ZIP 파일 이름 (확장자 제외)
    zip_name = '시체기사군터80화까지'
    # ZIP 파일 생성
    zip_folders(folder_paths, zip_name)
    
    shutdown_system()
