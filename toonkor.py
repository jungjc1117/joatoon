from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor
import platform
import zipfile  # zipfile 모듈 임포트

# Firefox 옵션 설정 (Headless 모드 포함)
options = Options()
options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
options.add_argument('--headless')  # Headless 모드로 브라우저 실행
options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0")

# geckodriver 경로를 설정
service = Service(r"C:\Users\jjc\Downloads\pythonWork\geckodriver32.exe")
driver = webdriver.Firefox(service=service, options=options)
wait = WebDriverWait(driver, 30)

# 이미지가 저장될 디렉토리 설정
download_dir = r"C:\Users\jjc\Downloads\pythonWork\downloaded"

# 페이지 접속
driver.get('https://toonkor429.com/%EC%9E%A5%EC%94%A8%EC%84%B8%EA%B0%80_%ED%98%B8%EC%9C%84%EB%AC%B4%EC%82%AC_1%ED%99%94.html')

def download_image(session, img_url, comic_dir, idx):
    try:
        img_data = session.get(img_url).content
        img_name = os.path.join(comic_dir, f"image_{idx+1}.jpg")
        with open(img_name, 'wb') as handler:
            handler.write(img_data)
        print(f"Downloaded: {img_name}")
    except Exception as e:
        print(f"이미지 다운로드 실패: {e}")

def download_images():
    # 이미지가 모두 로드될 때까지 대기
    images = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#toon_img img')))

    # 폴더 설정
    comic_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.toon-title'))).text
    comic_dir = os.path.join(download_dir, comic_name)
    
    if not os.path.exists(comic_dir):
        os.makedirs(comic_dir)

    # 세션 생성 및 이미지 병렬 다운로드
    session = requests.Session()
    with ThreadPoolExecutor(max_workers=10) as executor:
        for idx, img in enumerate(images):
            img_url = img.get_attribute('src')
            if img_url:
                executor.submit(download_image, session, img_url, comic_dir, idx)
    
    return comic_dir  # 다운로드한 폴더 경로 반환

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
    
def delete_folders(folder_paths):
    """
    주어진 폴더들을 삭제합니다.

    :param folder_paths: 삭제할 폴더들의 경로 리스트 (예: ['1화', '2화', ...])
    """
    for folder in folder_paths:
        try:
            if os.path.exists(folder):
                # 폴더 내부의 모든 파일과 하위 폴더 삭제
                for root, dirs, files in os.walk(folder, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                # 최종적으로 폴더 자체를 삭제
                os.rmdir(folder)
                print(f"Deleted folder: {folder}")
            else:
                print(f"Folder does not exist: {folder}")
        except Exception as e:
            print(f"Error deleting folder {folder}: {e}")

if __name__ == "__main__":
    folder_paths = []

    while True:
        try:
            comic_dir = download_images()
            folder_paths.append(comic_dir)
            next_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.btn-resource.btn-next.at-tip')))
            if next_button.is_displayed() and next_button.is_enabled():
                next_button.click()
            else:
                print("다음 버튼이 비활성화 상태입니다. 종료합니다.")
                break
            time.sleep(2)  # 페이지 로드를 위해 잠시 대기
        except Exception as e:
            print("더 이상 다음 버튼이 없습니다. 종료합니다.")
            print(f"오류: {str(e)}")
            break

    # 생성할 ZIP 파일 이름 (확장자 제외)
    zip_name = '장씨세가 호위무사'
    
    # ZIP 파일 생성
    zip_folders(folder_paths, zip_name)
    
    # 폴더 삭제
    delete_folders(folder_paths)
    
    # 드라이버 종료
    driver.quit()
