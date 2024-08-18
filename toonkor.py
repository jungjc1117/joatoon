from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import requests
import time

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
for i in range(77, 187):  # 예: 1부터 10까지
    # 순환할 URL 설정
    url = f"https://toonkor428.com/%EC%82%AC%EC%83%81%EC%B5%9C%EA%B0%95_{i}%ED%99%94.html"
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
