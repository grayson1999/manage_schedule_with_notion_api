import os
from html import escape
from dotenv import load_dotenv
from datetime import datetime
from .init import *
import requests
load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_API_URL: str = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
TELEGRAM_TEXT_LIMIT: int = 4096
PARSE_MODE: str = "HTML"


def send_message(text: str, parse_mode: str = PARSE_MODE) -> None:
    """Telegram Bot API로 메시지를 전송한다."""
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text[:TELEGRAM_TEXT_LIMIT],
        "parse_mode": parse_mode,
    }
    response = requests.post(TELEGRAM_API_URL, json=payload, timeout=10)
    response.raise_for_status()


def send_message_with_time(text: str) -> None:
    """타임스탬프를 포함하여 Telegram 메시지를 전송한다."""
    datetime_format = datetime.today().strftime("%Y-%m-%d %H:%M")
    send_message(f"[{datetime_format}] {escape(text)}", parse_mode="")


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
    lines = [f"<b>{escape(section_title)}</b>"]
    pre_lines = []
    for item in items:
        pct = min(item["rate"], 1.0) * 100
        bar = create_progress_bar(pct, length=bar_length)
        name = escape(item["name"])
        pre_lines.append(f"{name:<6} {item['achieved']}/{item['target']}  {bar} {pct:3.0f}%")

    lines.append("<pre>" + "\n".join(pre_lines) + "</pre>")
    return "\n".join(lines)


## 랜덤 명언 가져오기
def get_random_advice() -> tuple[str, str]:
    """명언과 저자를 튜플로 반환한다."""
    try:
        response = requests.get("https://korean-advice-open-api.vercel.app/api/advice", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("message", ""), data.get("author", "")
    except Exception:
        pass
    return "작은 습관이 모여 큰 변화를 만든다", ""


def _format_medicine_summary(medicine_stats: dict) -> str:
    """약 복용 등급별 요약을 한 줄로 포맷한다."""
    parts = []
    if medicine_stats["perfect"]:
        parts.append(f'🟢 완벽 {len(medicine_stats["perfect"])}개')
    if medicine_stats["good"]:
        parts.append(f'🟡 우수 {len(medicine_stats["good"])}개')
    if medicine_stats["need_improvement"]:
        parts.append(f'🔴 개선 {len(medicine_stats["need_improvement"])}개')
    return "  ".join(parts) if parts else "데이터 없음"


## 주간 리포트 생성
def create_weekly_report(achievement_rate, medicine_pages, week_name, routine_items: list[dict] | None = None):
    # 약 복용 현황 분석
    medicine_stats = categorize_medicine_by_completion(medicine_pages)
    medicine_percentage = (medicine_stats['total_taken'] / medicine_stats['total_possible'] * 100) if medicine_stats['total_possible'] > 0 else 0

    # 현재 시간
    datetime_format = datetime.today().strftime("%m-%d (%a) %H:%M")

    # 진행바 생성
    routine_pct = achievement_rate * 100
    routine_bar = create_progress_bar(routine_pct, length=15)
    medicine_bar = create_progress_bar(medicine_percentage, length=15)

    # 랜덤 명언 가져오기
    advice_msg, advice_author = get_random_advice()

    # 개별 루틴 현황 섹션
    per_item_section = ""
    if routine_items:
        per_item_section = "\n\n" + format_per_item_section(routine_items, "📋 개별 루틴 현황")
    else:
        per_item_section = "\n⚠️ 루틴 데이터가 없습니다. Notion DB를 확인하세요."

    # 약 복용 등급 요약
    medicine_summary = _format_medicine_summary(medicine_stats)

    # 명언 blockquote
    advice_line = escape(advice_msg)
    if advice_author:
        advice_line += f"\n— <i>{escape(advice_author)}</i>"

    # 리포트 생성 (Telegram HTML 최적화)
    report = (
        f"<b>📊 주간 루틴 리포트</b>\n"
        f"📅 {escape(week_name)}  ⏰ {datetime_format}\n"
        f"\n"
        f"<b>🎯 루틴 달성률</b>\n"
        f"<code>{routine_bar} {routine_pct:.1f}%</code>"
        f"{per_item_section}\n"
        f"\n"
        f"<b>💊 약 복용 현황</b> ({medicine_stats['medicine_count']}종)\n"
        f"<code>{medicine_bar} {medicine_percentage:.1f}%</code>\n"
        f"{medicine_summary}\n"
        f"\n"
        f"<b>✅ 완료 작업</b>\n"
        f" • 달성률 기록 저장\n"
        f" • 데이터 백업 완료\n"
        f" • DB 초기화 완료\n"
        f"\n"
        f"<blockquote>{advice_line}</blockquote>\n"
        f"🚀 새로운 한 주 시작! 화이팅! 💪"
    )

    return report


if __name__ == "__main__":
    from .achievement_tracker import calculate_per_item_achievement

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
    ]

    test_routine_items = calculate_per_item_achievement(test_medicine_pages, datelist)

    # 테스트 리포트 생성
    report = create_weekly_report(
        achievement_rate=0.857,
        medicine_pages=test_medicine_pages,
        week_name="3월 첫째 주",
        routine_items=test_routine_items,
    )

    print("\n=== 주간 리포트 미리보기 ===\n")
    print(report)
    print("\n=== 실제 Telegram 전송 테스트 ===")

    try:
        send_message(report)
        print("Telegram 메시지 전송 완료!")
    except Exception as e:
        print(f"Telegram 전송 실패: {e}")
