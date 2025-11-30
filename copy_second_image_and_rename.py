import os
import shutil
from typing import List

# --- 설정 변수 ---
# ⚠️ 상위 폴더(1폴더)의 경로를 지정하세요. 
# 스크립트가 실행되는 위치와 동일하다면 '.'을 사용합니다.
BASE_DIR = "." 
# 이미지 파일 확장자 리스트
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg')

def get_sorted_image_files(folder_path: str) -> List[str]:
    """
    주어진 폴더 경로에서 이미지 파일(png, jpg, jpeg) 목록을 얻어 오름차순으로 정렬합니다.
    """
    image_files = []
    
    # 폴더 내 모든 파일 및 폴더 목록 가져오기
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        # 파일이고, 확장자가 IMAGE_EXTENSIONS에 포함되는지 확인
        if os.path.isfile(item_path) and item.lower().endswith(IMAGE_EXTENSIONS):
            image_files.append(item)
    
    # 파일명을 기준으로 오름차순 정렬
    # '001.jpg', '002.jpg', '010.jpg' 순서로 정확하게 정렬됩니다.
    image_files.sort()
    return image_files

def copy_second_image_and_rename(base_directory: str):
    """
    상위 폴더 내의 각 하위 폴더에서 두 번째 이미지 파일을 복사하여 
    상위 폴더에 하위 폴더 이름으로 저장합니다.
    """
    print(f"--- 작업 시작: 상위 폴더 '{base_directory}' ---")
    
    # 상위 폴더 내의 모든 항목을 순회합니다.
    for folder_name in os.listdir(base_directory):
        # 상위 폴더 자체는 건너뜁니다.
        if folder_name == os.path.basename(__file__):
            continue

        sub_folder_path = os.path.join(base_directory, folder_name)

        # 1. 하위 폴더(2폴더)인지 확인합니다.
        if os.path.isdir(sub_folder_path):
            print(f"\n[처리 중] 폴더: {folder_name}")
            
            # 2. 이미지 파일 목록을 오름차순으로 정렬합니다.
            sorted_images = get_sorted_image_files(sub_folder_path)
            
            if len(sorted_images) < 2:
                print(f" -> 경고: '{folder_name}' 폴더에는 이미지가 2개 미만입니다. 건너뜁니다.")
                continue

            # 3. 두 번째 파일(인덱스 1)을 선택합니다.
            second_file_name = sorted_images[1]
            source_file_path = os.path.join(sub_folder_path, second_file_name)
            
            # 4. 새 파일명(하위 폴더명 + 원래 확장자)을 생성합니다.
            # .png, .jpg, .jpeg 등의 확장자를 유지합니다.
            file_extension = os.path.splitext(second_file_name)[1]
            new_file_name = f"{folder_name}{file_extension}"
            destination_file_path = os.path.join(base_directory, new_file_name)
            
            # 5. 파일을 상위 폴더(1폴더)에 복사하고 파일명을 변경합니다.
            try:
                shutil.copy2(source_file_path, destination_file_path) # copy2는 메타데이터 유지
                print(f" -> 원본: {second_file_name} (두 번째 파일)")
                print(f" -> 대상: {new_file_name}")
                print(f" -> ✅ 복사 완료: '{destination_file_path}'")
            except Exception as e:
                print(f" -> ❌ 오류 발생: 파일 복사 중 실패. ({e})")

    print("\n--- 모든 폴더 작업 완료 ---")


if __name__ == "__main__":
    copy_second_image_and_rename(BASE_DIR)
