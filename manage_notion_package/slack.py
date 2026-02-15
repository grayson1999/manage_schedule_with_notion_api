import slack_sdk
import os
from dotenv import load_dotenv
from datetime import datetime
from .init import *
import requests
load_dotenv()

SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_CHANNEL = "#notion"

def slack_message(msg):
    client = slack_sdk.WebClient(token = SLACK_TOKEN)
    client.chat_postMessage(
        channel=SLACK_CHANNEL,
        text=msg
        )
    
def slack_message_with_time(msg):
    datetime_format = datetime.today().strftime("%Y-%m-%d %H:%M")
    client = slack_sdk.WebClient(token = SLACK_TOKEN)
    client.chat_postMessage(
        channel=SLACK_CHANNEL,
        text="["+datetime_format+"] "+msg
        )

## 약 복용 현황을 등급별로 분류
def categorize_medicine_by_completion(medicine_pages):
    perfect = []  # 달성 개수 >= 목표 개수
    good = []     # 달성 개수 >= 목표 개수의 70%
    need_improvement = []  # 그 외

    total_taken = 0
    total_possible = 0

    for page in medicine_pages:
        page_props = page["properties"]
        title = page_props["이름"]["title"][0]["plain_text"]

        # 달성 개수 계산
        check_count = 0
        for date in datelist:
            if page_props[date]["checkbox"] == True:
                check_count += 1

        # 목표 개수 가져오기 (없으면 기본값 7)
        target_count = page_props.get("목표 개수", {}).get("number", 7) or 7

        total_taken += check_count
        total_possible += target_count

        if check_count >= target_count:
            perfect.append(title)
        elif check_count >= target_count * 0.7:
            good.append(title)
        else:
            need_improvement.append(title)

    return {
        'perfect': perfect,
        'good': good,
        'need_improvement': need_improvement,
        'total_taken': total_taken,
        'total_possible': total_possible,
        'medicine_count': len(medicine_pages)
    }

## 진행바 생성 함수
def create_progress_bar(percentage, length=20):
    filled = int(length * percentage / 100)
    empty = length - filled
    return "█" * filled + "▓" * empty

## 개별 항목 달성률 섹션 포맷
def format_per_item_section(
    items: list[dict],
    section_title: str = "개별 루틴 현황",
) -> str:
    """개별 항목별 달성 현황을 진행바와 함께 포맷한다."""
    if not items:
        return ""

    bar_length = 7
    lines = [section_title]
    for item in items:
        pct = min(item["rate"], 1.0) * 100
        bar = create_progress_bar(pct, length=bar_length)
        lines.append(f" \u2022 {item['name']:<6} {item['achieved']}/{item['target']}  {bar} {pct:.0f}%")

    return "\n".join(lines)


## 랜덤 명언 가져오기
def get_random_advice():
    try:
        response = requests.get("https://korean-advice-open-api.vercel.app/api/advice", timeout=5)
        if response.status_code == 200:
            data = response.json()
            author = data.get("author", "")
            message = data.get("message", "")

            return f'"{message}" - {author}'
        else:
            return '"작은 습관이 모여 큰 변화를 만든다"'
    except Exception as e:
        # API 실패 시 기본 명언 반환
        return '"작은 습관이 모여 큰 변화를 만든다"'

## 주간 리포트 생성
def create_weekly_report(achievement_rate, medicine_pages, week_name, routine_items: list[dict] | None = None):
    # 약 복용 현황 분석
    medicine_stats = categorize_medicine_by_completion(medicine_pages)
    medicine_percentage = (medicine_stats['total_taken'] / medicine_stats['total_possible'] * 100) if medicine_stats['total_possible'] > 0 else 0

    # 현재 시간
    datetime_format = datetime.today().strftime("%m-%d (%a) %H:%M")

    # 진행바 생성
    routine_bar = create_progress_bar(achievement_rate * 100, length=15)
    medicine_bar = create_progress_bar(medicine_percentage, length=15)

    # 랜덤 명언 가져오기
    advice = get_random_advice()

    # 개별 루틴 현황 섹션
    per_item_section = ""
    if routine_items:
        per_item_section = "\n" + format_per_item_section(routine_items, "📋 개별 루틴 현황")

    # 리포트 생성 (모바일 최적화 - 심플 버전)
    report = f"""━━━━━━━━━━━━━━━
📊 주간 루틴 완료 리포트
📅 {week_name}
⏰ {datetime_format}

🎯 루틴 달성률
{routine_bar} {achievement_rate * 100:.1f}%{per_item_section}

💊 약 복용 현황 ({medicine_stats['medicine_count']}종)
{medicine_bar} {medicine_percentage:.1f}%

🟢 완벽 {len(medicine_stats['perfect'])}개  🟡 우수 {len(medicine_stats['good'])}개  🔴 개선 {len(medicine_stats['need_improvement'])}개

✅ 완료 작업
 • 달성률 기록 저장
 • 데이터 백업 완료
 • DB 초기화 완료

💭 {advice}

🚀 새로운 한 주 시작! 화이팅! 💪
━━━━━━━━━━━━━━━"""

    return report


if __name__ == "__main__":
    # 테스트용 가짜 약 데이터 생성
    test_medicine_pages = [
        {
            "properties": {
                "이름": {"title": [{"plain_text": "비타민D"}]},
                "목표 개수": {"number": 7},
                "Mon": {"checkbox": True},
                "Tue": {"checkbox": True},
                "Wed": {"checkbox": True},
                "Thur": {"checkbox": True},
                "Fri": {"checkbox": True},
                "Sat": {"checkbox": True},
                "Sun": {"checkbox": True}
            }
        },
        {
            "properties": {
                "이름": {"title": [{"plain_text": "오메가3"}]},
                "목표 개수": {"number": 7},
                "Mon": {"checkbox": True},
                "Tue": {"checkbox": True},
                "Wed": {"checkbox": True},
                "Thur": {"checkbox": True},
                "Fri": {"checkbox": True},
                "Sat": {"checkbox": True},
                "Sun": {"checkbox": False}
            }
        },
        {
            "properties": {
                "이름": {"title": [{"plain_text": "종합비타민"}]},
                "목표 개수": {"number": 5},
                "Mon": {"checkbox": True},
                "Tue": {"checkbox": True},
                "Wed": {"checkbox": True},
                "Thur": {"checkbox": True},
                "Fri": {"checkbox": True},
                "Sat": {"checkbox": False},
                "Sun": {"checkbox": False}
            }
        },
        {
            "properties": {
                "이름": {"title": [{"plain_text": "마그네슘"}]},
                "목표 개수": {"number": 7},
                "Mon": {"checkbox": True},
                "Tue": {"checkbox": True},
                "Wed": {"checkbox": True},
                "Thur": {"checkbox": True},
                "Fri": {"checkbox": True},
                "Sat": {"checkbox": False},
                "Sun": {"checkbox": False}
            }
        },
        {
            "properties": {
                "이름": {"title": [{"plain_text": "유산균"}]},
                "목표 개수": {"number": 3},
                "Mon": {"checkbox": True},
                "Tue": {"checkbox": True},
                "Wed": {"checkbox": True},
                "Thur": {"checkbox": False},
                "Fri": {"checkbox": False},
                "Sat": {"checkbox": False},
                "Sun": {"checkbox": False}
            }
        }
    ]

    # 테스트 리포트 생성
    test_achievement_rate = 0.857  # 85.7%
    test_week_name = "12월 첫째 주"

    # 리포트 출력 (콘솔에서 확인)
    report = create_weekly_report(
        achievement_rate=test_achievement_rate,
        medicine_pages=test_medicine_pages,
        week_name=test_week_name
    )

    print("\n=== 주간 리포트 미리보기 ===\n")
    print(report)
    print("\n=== 실제 Slack 전송 테스트 ===")

    # 실제 Slack으로 전송 (SLACK_TOKEN이 설정되어 있는 경우만)
    try:
        slack_message(report)
        print("✅ Slack 메시지 전송 완료!")
    except Exception as e:
        print(f"❌ Slack 전송 실패: {e}")
        print("(SLACK_TOKEN이 설정되지 않았거나 유효하지 않을 수 있습니다)")