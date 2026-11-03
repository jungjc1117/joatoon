import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import winsound

def download_all_webtoon_episodes():
  # 1. 크롬 드라이버 설정
  options = webdriver.ChromeOptions()
  # options.add_argument('--headless')  # 브라우저 창을 띄우지 않으려면 주석 해제
  options.add_argument("--disable-gpu")
  options.add_argument("no-sandbox")

  driver = webdriver.Chrome(
      service=Service(ChromeDriverManager().install()), options=options
  )

  try:
    # 2. 웹툰 목록 페이지 접속
    list_url = "https://blacktoon426.com/webtoon/8868.html"
    print(f"목록 페이지 접속 중: {list_url}")
    driver.get(list_url)
    time.sleep(3)

    # 3. 목록 페이지 하단 끝까지 스크롤하여 모든 에피소드 로드
    print("목록의 모든 에피소드를 불러오기 위해 스크롤을 진행합니다...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
      driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
      time.sleep(1.5)  # 컨텐츠 로딩 대기 시간
      new_height = driver.execute_script("return document.body.scrollHeight")
      if new_height == last_height:
        # 높이가 더 이상 변하지 않으면 최하단 도달
        break
      last_height = new_height
    print("목록 전체 로드 완료!")

    # 4. 완전히 로드된 모든 에피소드 카드 요소들 찾기
    cards = driver.find_elements(
        By.CSS_SELECTOR, "div.card.card-fluid.mt-2.toon-link-s"
    )
    print(f"총 {len(cards)}개의 에피소드를 발견했습니다.")

    # 각 에피소드 카드 정보 미리 수집 (상세 페이지로 이동하면 기존 드라이버 컨텍스트가 바뀌므로 리스트에 저장)
    episode_tasks = []
    for card in cards:
      try:
        a_tag = card.find_element(By.TAG_NAME, "a")
        href = a_tag.get_attribute("href")

        p_tag = card.find_element(By.TAG_NAME, "p")
        # <p> 태그 내부의 전체 텍스트 (예: "0150 - 완결 후기 \n 2024-01-08")
        raw_text = p_tag.text.strip()

        # 첫 번째 줄(제목 부분)만 가져오기 (날짜 제외)
        title_line = raw_text.split("\n")[0].strip()

        # 윈도우/맥 폴더명으로 사용할 수 없는 특수문자 제거
        folder_name = "".join(
            c for c in title_line if c.isalnum() or c in (" ", "-", "_", ".")
        ).strip()

        if href and folder_name:
          episode_tasks.append({"href": href, "folder_name": folder_name})
      except Exception as e:
        print(f"에피소드 정보 추출 중 에러: {e}")
        continue

    # 5. 각 에피소드별로 순회하며 이미지 다운로드 수행
    for idx, task in enumerate(episode_tasks, start=1):
      target_href = task["href"]
      folder_name = task["folder_name"]

      print(
          f"\n--- [{idx}/{len(episode_tasks)}] 처리 중: {folder_name} ---"
      )
      print(f"이동할 링크: {target_href}")

      # 상세 페이지 이동
      driver.get(target_href)
      time.sleep(2)

      # 상세 페이지 스크롤을 내려서 내부 이미지(Lazy Load) 모두 로드
      detail_last_height = driver.execute_script(
          "return document.body.scrollHeight"
      )
      while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.2)
        detail_new_height = driver.execute_script(
            "return document.body.scrollHeight"
        )
        if detail_new_height == detail_last_height:
          break
        detail_last_height = detail_new_height

      # 이미지 태그 수집
      img_elements = driver.find_elements(
          By.CSS_SELECTOR, "#toon_content_imgs img"
      )
      img_urls = []
      for img in img_elements:
        src = (
            img.get_attribute("data-original")
            or img.get_attribute("o_src")
            or img.get_attribute("src")
        )
        if src:
          img_urls.append(src)

      print(f"수집된 이미지 개수: {len(img_urls)}개")

      if not img_urls:
        print("이미지가 없어 건너뜁니다.")
        continue

      # 폴더 생성 (<p> 태그에서 추출한 이름 사용)
      if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"폴더 생성 완료: '{folder_name}'")

      headers = {
          "User-Agent": (
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
              " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
          ),
          "Referer": target_href,
      }

      # 이미지 다운로드 및 일련번호 저장 (0001.jpg, 0002.jpg...)
      for img_idx, img_url in enumerate(img_urls, start=1):
        try:
          response = requests.get(img_url, headers=headers, stream=True)
          if response.status_code == 200:
            file_path = os.path.join(folder_name, f"{img_idx:04d}.jpg")
            with open(file_path, "wb") as f:
              for chunk in response.iter_content(1024):
                f.write(chunk)
          else:
            print(f"다운로드 실패 (코드 {response.status_code}): {img_url}")
        except Exception as e:
          print(f"이미지 다운로드 에러: {e}")

      print(f"'{folder_name}' 에피소드 다운로드 완료!")
      time.sleep(1)

    print("\n모든 에피소드 다운로드 작업이 완료되었습니다!")

  finally:
    driver.quit()


if __name__ == "__main__":
  download_all_webtoon_episodes()
  winsound.Beep(2000, 1000)
