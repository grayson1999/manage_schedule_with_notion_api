"""개별 항목별 달성률 계산 및 Notion 비고 컬럼용 JSON 빌드 모듈."""
import json
from datetime import datetime
from .logger import logger


DEFAULT_TARGET = 7
NOTION_RICH_TEXT_LIMIT = 2000


def calculate_per_item_achievement(
    pages: list[dict],
    datelist: list[str],
    default_target: int = DEFAULT_TARGET,
    title_key: str = "이름",
    target_key: str = "목표 개수",
) -> list[dict]:
    """각 page의 항목별 달성 현황을 계산한다.

    Args:
        title_key: 제목 속성명 (DB마다 다를 수 있음, 예: "이름", "할일")
        target_key: 목표 개수 속성명 (예: "목표 개수", "달성 목표(횟수)")

    Returns:
        [{"name": str, "category": str, "achieved": int,
          "target": int, "rate": float, "days": list[str]}]
    """
    if not pages:
        logger.warning("calculate_per_item_achievement: 입력된 페이지가 비어있습니다")
        return []

    items: list[dict] = []
    skipped_count = 0

    for page in pages:
        props = page["properties"]

        title_data = props.get(title_key, {}).get("title", [])
        if not title_data:
            skipped_count += 1
            continue
        name = title_data[0].get("plain_text", "Unknown")

        # 분류(select) - 없으면 빈 문자열
        category_data = props.get("분류", {}).get("select")
        category = category_data["name"] if category_data else ""

        # 목표 개수 (없으면 default_target)
        target = props.get(target_key, {}).get("number") or default_target

        # 요일별 체크 여부 집계
        achieved = 0
        checked_days: list[str] = []
        for date in datelist:
            if props.get(date, {}).get("checkbox", False):
                achieved += 1
                checked_days.append(date)

        rate = round(achieved / target, 4) if target > 0 else 0.0

        items.append({
            "name": name,
            "category": category,
            "achieved": achieved,
            "target": target,
            "rate": rate,
            "days": checked_days,
        })

    if skipped_count > 0:
        logger.info(f"제목 없는 페이지 {skipped_count}개 건너뜀")
    logger.info(f"항목 {len(items)}개 계산 완료")
    return items


def build_achievement_note(
    routine_items: list[dict],
    medicine_items: list[dict],
) -> str:
    """항목별 달성 데이터를 Notion 비고 컬럼용 JSON 문자열로 변환한다.

    Notion rich_text 2000자 제한 대응: days 필드 제외.
    """
    now = datetime.now()
    iso_year, iso_week, _ = now.isocalendar()

    def _compact(items: list[dict]) -> list[dict]:
        return [
            {
                "name": item["name"],
                "achieved": item["achieved"],
                "target": item["target"],
                "rate": item["rate"],
            }
            for item in items
        ]

    # medicine은 전체 달성률만 단일 숫자로 포함
    total_achieved = sum(i["achieved"] for i in medicine_items)
    total_target = sum(i["target"] for i in medicine_items)
    medicine_rate = round(total_achieved / total_target, 4) if total_target > 0 else 0.0

    note = {
        "date": now.strftime("%Y-%m-%d"),
        "iso_week": f"{iso_year}-W{iso_week:02d}",
        "routine": _compact(routine_items),
        "medicine_rate": medicine_rate,
    }

    result = json.dumps(note, ensure_ascii=False)

    if len(result) > NOTION_RICH_TEXT_LIMIT:
        note["routine"] = [{"name": i["name"], "rate": i["rate"]} for i in routine_items]
        result = json.dumps(note, ensure_ascii=False)

    return result[:NOTION_RICH_TEXT_LIMIT]


if __name__ == "__main__":
    from init import datelist

    # 테스트용 루틴 데이터
    test_routine_pages = [
        {
            "properties": {
                "이름": {"title": [{"plain_text": "운동"}]},
                "분류": {"select": {"name": "건강"}},
                "목표 개수": {"number": 7},
                "Mon": {"checkbox": True},
                "Tue": {"checkbox": True},
                "Wed": {"checkbox": True},
                "Thur": {"checkbox": True},
                "Fri": {"checkbox": True},
                "Sat": {"checkbox": False},
                "Sun": {"checkbox": False},
            }
        },
        {
            "properties": {
                "이름": {"title": [{"plain_text": "독서"}]},
                "분류": {"select": {"name": "자기계발"}},
                "목표 개수": {"number": 5},
                "Mon": {"checkbox": True},
                "Tue": {"checkbox": True},
                "Wed": {"checkbox": True},
                "Thur": {"checkbox": False},
                "Fri": {"checkbox": False},
                "Sat": {"checkbox": False},
                "Sun": {"checkbox": False},
            }
        },
    ]

    test_medicine_pages = [
        {
            "properties": {
                "이름": {"title": [{"plain_text": "비타민D"}]},
                "분류": {"select": None},
                "목표 개수": {"number": 7},
                "Mon": {"checkbox": True},
                "Tue": {"checkbox": True},
                "Wed": {"checkbox": True},
                "Thur": {"checkbox": True},
                "Fri": {"checkbox": True},
                "Sat": {"checkbox": True},
                "Sun": {"checkbox": True},
            }
        },
    ]

    routine_items = calculate_per_item_achievement(test_routine_pages, datelist)
    medicine_items = calculate_per_item_achievement(test_medicine_pages, datelist)

    print("=== Routine Items ===")
    for item in routine_items:
        print(f"  {item['name']}: {item['achieved']}/{item['target']} ({item['rate']*100:.1f}%)")

    print("\n=== Medicine Items ===")
    for item in medicine_items:
        print(f"  {item['name']}: {item['achieved']}/{item['target']} ({item['rate']*100:.1f}%)")

    note = build_achievement_note(routine_items, medicine_items)
    print(f"\n=== Achievement Note (JSON) ===\n{note}")
