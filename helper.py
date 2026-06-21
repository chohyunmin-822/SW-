import datetime
import unicodedata
import os
from typing import List

# ==========================================
# 터미널 디자인을 위한 ANSI 색상 코드 정의
# ==========================================
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Windows 터미널에서 ANSI 이스케이프 코드를 활성화하기 위한 초기화 코드
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

# ==========================================
# 데이터 모델 정의 (클래스 구조)
# ==========================================

class Ingredient:
    """식재료 개별 데이터를 나타내는 클래스"""
    
    def __init__(self, name: str, purchase_date: str, expiration_date: str, location: str):
        self.name = name
        self.purchase_date = purchase_date
        self.expiration_date = expiration_date
        self.location = location  # '냉장' 또는 '냉동'

    @property
    def days_left(self) -> int:
        """오늘 날짜 기준으로 유통기한까지 남은 일수를 계산하여 반환합니다."""
        today = datetime.date.today()
        exp_date = datetime.datetime.strptime(self.expiration_date, '%Y-%m-%d').date()
        return (exp_date - today).days

    @property
    def is_urgent(self) -> bool:
        """유통기한이 3일 이하로 남았거나 이미 경과했는지(임박 상태) 여부를 반환합니다."""
        return self.days_left <= 3


class Refrigerator:
    """식재료 목록을 관리하고 CRUD 및 정렬 로직을 처리하는 클래스"""
    
    def __init__(self):
        self.ingredients: List[Ingredient] = []

    def register(self, name: str, purchase_date: str, expiration_date: str, location: str) -> Ingredient:
        """새로운 식재료를 등록합니다."""
        item = Ingredient(name, purchase_date, expiration_date, location)
        self.ingredients.append(item)
        return item

    def delete(self, original_index: int) -> Ingredient:
        """지정한 원본 인덱스의 식재료를 냉장고에서 삭제합니다."""
        return self.ingredients.pop(original_index)

    def get_sorted_list(self) -> List[dict]:
        """유통기한 임박 식재료가 최상단에 오도록 정렬된 식재료 정보 리스트를 반환합니다.
        
        정렬 알고리즘 작동 원리:
        - 1순위: 임박 여부 x.is_urgent (True인 임박 항목을 가장 먼저 출력하기 위해 `not x.is_urgent` 사용)
          (not True -> 0, not False -> 1 이므로 오름차순 정렬 시 0(임박)이 최상단으로 정렬됨)
        - 2순위: 남은 일수 x.days_left (남은 기간이 가장 촉박하거나 많이 지난 식재료 순서로 오름차순 정렬)
        """
        # 정렬된 리스트와 원본 리스트의 인덱스 정보를 함께 담아 튜플/딕셔너리 형태로 가공하여 반환
        processed = []
        for idx, item in enumerate(self.ingredients):
            processed.append({
                "original_index": idx,
                "item": item
            })
            
        # 람다(lambda) 다중 정렬 적용
        processed.sort(key=lambda x: (not x["item"].is_urgent, x["item"].days_left))
        return processed

# ==========================================
# 한글 정렬 깨짐 방지를 위한 헬퍼 함수
# ==========================================

def get_visual_width(text: str) -> int:
    """문자열의 시각적 너비(터미널에서의 출력 너비)를 계산합니다.
    한글 등 전각 문자는 2칸, 영문/숫자 등 반각 문자는 1칸으로 계산하며 ANSI 색상 코드는 제외합니다.
    """
    clean_text = text
    for code in [RESET, BOLD, RED, GREEN, YELLOW, BLUE, CYAN, WHITE]:
        clean_text = clean_text.replace(code, "")
        
    width = 0
    for char in clean_text:
        if unicodedata.east_asian_width(char) in ('W', 'F', 'A'):
            width += 2
        else:
            width += 1
    return width

def pad_string(text: str, target_width: int, align: str = 'left') -> str:
    """한글 너비를 고려하여 터미널 정렬용 공백을 추가(패딩)합니다."""
    current_width = get_visual_width(text)
    padding_needed = max(0, target_width - current_width)
    
    if align == 'left':
        return text + ' ' * padding_needed
    elif align == 'right':
        return ' ' * padding_needed + text
    else:  # center
        left_pad = padding_needed // 2
        right_pad = padding_needed - left_pad
        return ' ' * left_pad + text + ' ' * right_pad

def validate_date(date_text: str) -> bool:
    """입력받은 날짜 문자열이 YYYY-MM-DD 포맷에 맞는지 검증합니다."""
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# ==========================================
# CLI 사용자 인터페이스 구현
# ==========================================

def run_cli():
    # 냉장고 매니저 객체 생성
    fridge = Refrigerator()
    today = datetime.date.today()

    # ------------------------------------------
    # 샘플 데이터 초기 로딩 (PRD 요구사항)
    # ------------------------------------------
    # 1. 우유: 5일 전 구매, 1일 뒤 유통기한 만료 (유통기한 임박!)
    sample_1_purchase = (today - datetime.timedelta(days=5)).strftime('%Y-%m-%d')
    sample_1_expiry = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    fridge.register("우유", sample_1_purchase, sample_1_expiry, "냉장")

    # 2. 두부: 2일 전 구매, 3일 뒤 유통기한 만료 (유통기한 임박!)
    sample_2_purchase = (today - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
    sample_2_expiry = (today + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
    fridge.register("두부", sample_2_purchase, sample_2_expiry, "냉장")

    # 3. 양파: 7일 전 구매, 15일 뒤 유통기한 만료 (안전 상태)
    sample_3_purchase = (today - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    sample_3_expiry = (today + datetime.timedelta(days=15)).strftime('%Y-%m-%d')
    fridge.register("양파", sample_3_purchase, sample_3_expiry, "냉동")

    while True:
        print(f"\n{BOLD}{GREEN}★ 자취생의 든든한 파트너 [냉장고 파먹기 도우미] ★{RESET}")
        print(f"{WHITE}1. 🥦 새 식재료 등록 (식재료 추가){RESET}")
        print(f"{WHITE}2. 🔍 냉장고 조회 (유통기한 정렬 & 임박 경고){RESET}")
        print(f"{WHITE}3. 🗑️ 식재료 삭제 (요리 완료 및 비우기){RESET}")
        print(f"{WHITE}4. ❌ 프로그램 종료{RESET}")
        print(f"{BOLD}{GREEN}-------------------------------------------{RESET}")
        
        choice = input("원하는 메뉴 번호를 입력하세요 (1~4): ").strip()
        
        if choice == '1':
            print(f"\n{BOLD}{CYAN}=== 🥦 새 식재료 등록 ==={RESET}")
            
            # 식재료명 입력
            name = input("식재료 이름: ").strip()
            while not name:
                print(f"{RED}이름은 비어둘 수 없습니다.{RESET}")
                name = input("식재료 이름: ").strip()
                
            # 구매일 입력
            while True:
                purchase_date = input("구매일 (YYYY-MM-DD) [엔터 입력 시 오늘 날짜]: ").strip()
                if not purchase_date:
                    purchase_date = today.strftime('%Y-%m-%d')
                    break
                if validate_date(purchase_date):
                    break
                print(f"{RED}올바른 날짜 형식이 아닙니다. (예: 2026-06-21){RESET}")
                
            # 유통기한 입력
            while True:
                expiration_date = input("유통기한 (YYYY-MM-DD): ").strip()
                if validate_date(expiration_date):
                    p_date = datetime.datetime.strptime(purchase_date, '%Y-%m-%d').date()
                    e_date = datetime.datetime.strptime(expiration_date, '%Y-%m-%d').date()
                    if e_date >= p_date:
                        break
                    else:
                        print(f"{RED}유통기한은 구매일보다 빠를 수 없습니다. (구매일: {purchase_date}){RESET}")
                else:
                    print(f"{RED}올바른 날짜 형식이 아닙니다. (예: 2026-06-25){RESET}")
                    
            # 보관 위치 입력
            while True:
                location = input("보관 장소 (1: 냉장, 2: 냉동): ").strip()
                if location in ('1', '냉장'):
                    location = "냉장"
                    break
                elif location in ('2', '냉동'):
                    location = "냉동"
                    break
                print(f"{RED}1(냉장) 또는 2(냉동)를 입력해 주세요.{RESET}")
                
            fridge.register(name, purchase_date, expiration_date, location)
            print(f"\n{GREEN}✔ 식재료 '{name}'가 성공적으로 등록되었습니다!{RESET}")
            
        elif choice == '2':
            if not fridge.ingredients:
                print(f"\n{YELLOW}냉장고가 텅 비어 있습니다! 식재료를 등록해 주세요. 🧊{RESET}")
                continue
                
            sorted_data = fridge.get_sorted_list()
            
            print(f"\n{BOLD}{CYAN}========================================================================{RESET}")
            print(f"{BOLD}{WHITE}                   🧊 현재 냉장고 내 식재료 목록 🧊{RESET}")
            print(f"{BOLD}{CYAN}========================================================================{RESET}")
            
            # 테이블 헤더 포맷팅
            header = (
                f"│ {pad_string('번호', 4, 'center')} │ "
                f"{pad_string('식재료명', 14, 'center')} │ "
                f"{pad_string('보관', 6, 'center')} │ "
                f"{pad_string('구매일', 12, 'center')} │ "
                f"{pad_string('유통기한', 12, 'center')} │ "
                f"{pad_string('남은기한', 10, 'center')} │ "
                f"{pad_string('상태 경고', 18, 'center')} │"
            )
            print(header)
            print(f"├──────┼────────────────┼────────┼──────────────┼──────────────┼────────────┼────────────────────┤")
            
            # 데이터 행 출력
            for display_idx, entry in enumerate(sorted_data, start=1):
                item = entry["item"]
                loc_colored = f"{BLUE}{item.location}{RESET}" if item.location == "냉장" else f"{CYAN}{item.location}{RESET}"
                
                # 유통기한 경고 시각화 로직
                days_str = f"{item.days_left}일"
                if item.days_left < 0:
                    status_warning = f"{RED}⚠️ 기간 초과!{RESET}"
                    days_str = f"{RED}{abs(item.days_left)}일 지남{RESET}"
                elif item.days_left <= 3:
                    status_warning = f"{YELLOW}⚠️ 유통기한 임박!{RESET}"
                    days_str = f"{YELLOW}{item.days_left}일 남음{RESET}"
                else:
                    status_warning = f"{GREEN}정상 (안전){RESET}"
                    days_str = f"{item.days_left}일 남음"
                    
                row = (
                    f"│ {pad_string(str(display_idx), 4, 'center')} │ "
                    f"{pad_string(item.name, 14, 'left')} │ "
                    f"{pad_string(loc_colored, 6, 'center')} │ "
                    f"{pad_string(item.purchase_date, 12, 'center')} │ "
                    f"{pad_string(item.expiration_date, 12, 'center')} │ "
                    f"{pad_string(days_str, 10, 'right')} │ "
                    f"{pad_string(status_warning, 18, 'left')} │"
                )
                print(row)
                
            print(f"{BOLD}{CYAN}========================================================================{RESET}")
            print(f"💡 {YELLOW}노란색 ⚠️{RESET} 표시는 유통기한이 {YELLOW}3일 이하{RESET}로 남은 재료이며, 리스트 최상단에 노출됩니다.")
            
        elif choice == '3':
            if not fridge.ingredients:
                print(f"\n{YELLOW}냉장고에 삭제할 식재료가 없습니다.{RESET}")
                continue
                
            # 화면 출력을 한 뒤 삭제하도록 함
            sorted_data = fridge.get_sorted_list()
            print(f"\n{BOLD}{CYAN}========================================================================{RESET}")
            print(f"{BOLD}{WHITE}                   🗑️ 삭제 대상을 선택해 주세요{RESET}")
            print(f"{BOLD}{CYAN}========================================================================{RESET}")
            
            for display_idx, entry in enumerate(sorted_data, start=1):
                item = entry["item"]
                print(f"[{display_idx}] {item.name} (유통기한: {item.expiration_date} | {item.location})")
            print(f"{BOLD}{CYAN}========================================================================{RESET}")
            
            try:
                choice_idx = input("삭제할 식재료의 번호를 입력하세요 (취소하려면 엔터): ").strip()
                if not choice_idx:
                    print("삭제 작업이 취소되었습니다.")
                    continue
                    
                idx = int(choice_idx)
                if 1 <= idx <= len(sorted_data):
                    target = sorted_data[idx - 1]
                    # 원본 인덱스로 냉장고 관리 객체에서 식재료 삭제
                    deleted = fridge.delete(target["original_index"])
                    print(f"\n{GREEN}✔ '{deleted.name}' 재료가 정상적으로 냉장고에서 삭제되었습니다!{RESET}")
                else:
                    print(f"{RED}범위를 벗어난 번호입니다.{RESET}")
            except ValueError:
                print(f"{RED}올바른 번호를 입력해 주세요.{RESET}")
                
        elif choice == '4':
            print(f"\n{BOLD}{CYAN}냉장고 파먹기 도우미를 종료합니다. 오늘도 즐거운 냉파 생활 되세요! 🍳{RESET}\n")
            break
        else:
            print(f"\n{RED}잘못된 선택입니다. 1에서 4 사이의 숫자를 입력해 주세요.{RESET}")

if __name__ == "__main__":
    run_cli()
