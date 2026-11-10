import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def download_webtoon_episodes(driver, list_url):
    print(f"\n{'='*50}")
    print(f"웹툰 목록 페이지 접속 중: {list_url}")
    print(f"{'='*50}")
    driver.get(list_url)
    time.sleep(3)

    # 1. 웹툰 상위 폴더 이름 결정
    try:
        webtoon_title_elem = driver.find_element(By.CSS_SELECTOR, "h1, h2, .toon-title, .detail-title")
        webtoon_folder = "".join(c for c in webtoon_title_elem.text.strip() if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        if not webtoon_folder:
            raise Exception("제목을 찾을 수 없음")
    except:
        webtoon_folder = list_url.rstrip("/").split("/")[-1].replace(".html", "")

    if not os.path.exists(webtoon_folder):
        os.makedirs(webtoon_folder)
        print(f"웹툰 상위 폴더 생성 완료: '{webtoon_folder}'")

    # 2. [개선] 목록 페이지 스크롤 무한 루프 방지 (최대 50회 제한)
    print("목록의 모든 에피소드를 불러오기 위해 스크롤을 진행합니다...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_scrolls = 50 
    
    while scroll_attempts < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_attempts += 1
    print("목록 로드 시도 완료!")

    # 3. 에피소드 카드 요소들 수집
    cards = driver.find_elements(By.CSS_SELECTOR, "div.card.card-fluid.mt-2.toon-link-s")
    print(f"총 {len(cards)}개의 에피소드를 발견했습니다.")

    episode_tasks = []
    for card in cards:
        try:
            a_tag = card.find_element(By.TAG_NAME, "a")
            href = a_tag.get_attribute("href")
            p_tag = card.find_element(By.TAG_NAME, "p")
            raw_text = p_tag.text.strip()
            title_line = raw_text.split("\n")[0].strip()
            folder_name = "".join(c for c in title_line if c.isalnum() or c in (' ', '-', '_', '.')).strip()

            if href and folder_name:
                episode_tasks.append({"href": href, "folder_name": folder_name})
        except Exception as e:
            continue

    session = requests.Session()

    # 4. 각 에피소드별로 순회하며 이미지 다운로드 수행
    for idx, task in enumerate(episode_tasks, start=1):
        target_href = task["href"]
        ep_folder_name = task["folder_name"]
        save_dir = os.path.join(webtoon_folder, ep_folder_name)

        print(f"\n--- [{idx}/{len(episode_tasks)}] 처리 중: {ep_folder_name} ---")
        driver.get(target_href)
        time.sleep(2)

        # [개선] 본문 페이지 스크롤 무한 루프 방지 (최대 30회 제한)
        detail_last_height = driver.execute_script("return document.body.scrollHeight")
        detail_scroll_attempts = 0
        max_detail_scrolls = 30
        
        while detail_scroll_attempts < max_detail_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.2)
            detail_new_height = driver.execute_script("return document.body.scrollHeight")
            if detail_new_height == detail_last_height:
                break
            detail_last_height = detail_new_height
            detail_scroll_attempts += 1

        # 이미지 태그 수집
        img_elements = driver.find_elements(By.CSS_SELECTOR, "#toon_content_imgs img")
        img_urls = []
        for img in img_elements:
            src = img.get_attribute("data-original") or img.get_attribute("o_src") or img.get_attribute("src")
            if src:
                img_urls.append(src)

        print(f"수집된 이미지 개수: {len(img_urls)}개")

        if not img_urls:
            continue

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": target_href
        }

        # 이미지 다운로드
        for img_idx, img_url in enumerate(img_urls, start=1):
            file_path = os.path.join(save_dir, f"{img_idx:04d}.jpg")
            
            # 이미 다운로드한 파일이 있다면 중복 다운로드 방지 (RAM 및 대역폭 절약)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                continue

            for attempt in range(3):
                try:
                    response = session.get(img_url, headers=headers, stream=True, timeout=10)
                    if response.status_code == 200:
                        with open(file_path, "wb") as f:
                            for chunk in response.iter_content(4096): # 청크 크기를 4KB로 늘려 I/O 부하 감소
                                f.write(chunk)
                        break
                except Exception:
                    time.sleep(1)
            time.sleep(0.1)

        print(f"'{ep_folder_name}' 에피소드 다운로드 완료!")


def create_driver():
    """크롬 드라이버를 생성하는 헬퍼 함수"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')  # [개선] Headless 모드 필수 활성화 (RAM 절약의 핵심)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")  # [개선] 리눅스 공유메모리 부족 에러 방지
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )
    return driver


def main():
    webtoon_urls = [
        # "https://blacktoon427.com/webtoon/11677.html",
        # "https://blacktoon427.com/webtoon/3044.html",
        "https://blacktoon427.com/webtoon/4525.html",
        "https://blacktoon427.com/webtoon/3526.html",
        "https://blacktoon427.com/webtoon/4173.html",
    ]

    # [개선] 하나의 드라이버로 계속 쓰지 않고, 웹툰(큰 단위)이 바뀔 때마다 드라이버를 새로 켭니다.
    for url in webtoon_urls:
        print(f"\n>>> 새 드라이버 세션 시작 (메모리 최적화) <<<")
        driver = create_driver()
        try:
            download_webtoon_episodes(driver, url)
        except Exception as e:
            print(f"웹툰 처리 중 에러 발생 ({url}): {e}")
        finally:
            driver.quit()  # 하나의 웹툰이 끝나면 브라우저를 완전히 닫아 누적된 RAM을 반환합니다.
            time.sleep(2)

    print("\n모든 웹툰의 다운로드 작업이 완료되었습니다!")


if __name__ == "__main__":
    main()
    # 우분투 환경에서 beep 명령어가 없을 때 에러 나는 것을 방지하기 위해 예외처리
    try:
        os.system("beep -f 2000 -l 1000")
    except:
        pass
