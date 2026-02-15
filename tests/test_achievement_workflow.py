"""주차, 달성률, 비고가 Notion DB에 올바르게 들어가는지 검증하는 단위 테스트."""
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

DATELIST = ["Mon", "Tue", "Wed", "Thur", "Fri", "Sat", "Sun"]


def make_routine_page(name: str, category: str, target: int, checks: list[bool]) -> dict:
    """테스트용 루틴 page 데이터를 생성한다."""
    props = {
        "이름": {"title": [{"plain_text": name}]},
        "분류": {"select": {"name": category} if category else None},
        "목표 개수": {"number": target},
        "완료 여부": {"formula": {"boolean": all(checks[:target])}},
    }
    for i, day in enumerate(DATELIST):
        props[day] = {"checkbox": checks[i] if i < len(checks) else False}
    return {"id": f"page-{name}", "properties": props}


def make_achievement_page() -> dict:
    """테스트용 달성률 DB page 데이터를 생성한다."""
    return {
        "id": "achi-page-1",
        "properties": {
            "주차": {"type": "title", "title": [{"text": {"content": "2월 둘째 주"}}]},
            "달성률": {"type": "number", "number": 0.5},
        },
    }


# ─── 테스트 데이터 ───
ROUTINE_PAGES = [
    make_routine_page("운동", "건강", 7, [True, True, True, True, True, False, False]),
    make_routine_page("독서", "자기계발", 5, [True, True, True, False, False, False, False]),
    make_routine_page("영어", "공부", 7, [True, True, True, True, True, True, True]),
]

MEDICINE_PAGES = [
    make_routine_page("비타민D", "", 7, [True, True, True, True, True, True, True]),
    make_routine_page("오메가3", "", 7, [True, True, True, True, True, True, False]),
]


class TestCalculatePerItemAchievement(unittest.TestCase):
    """achievement_tracker.calculate_per_item_achievement 단위 테스트."""

    def setUp(self):
        from manage_notion_package.achievement_tracker import calculate_per_item_achievement
        self.calc = calculate_per_item_achievement

    def test_basic_calculation(self):
        """정상 케이스: 달성 개수, 목표, 달성률 계산."""
        items = self.calc(ROUTINE_PAGES, DATELIST)

        self.assertEqual(len(items), 3)

        # 운동: 5/7
        self.assertEqual(items[0]["name"], "운동")
        self.assertEqual(items[0]["achieved"], 5)
        self.assertEqual(items[0]["target"], 7)
        self.assertAlmostEqual(items[0]["rate"], 5 / 7, places=4)

        # 독서: 3/5
        self.assertEqual(items[1]["name"], "독서")
        self.assertEqual(items[1]["achieved"], 3)
        self.assertEqual(items[1]["target"], 5)
        self.assertAlmostEqual(items[1]["rate"], 3 / 5, places=4)

        # 영어: 7/7
        self.assertEqual(items[2]["name"], "영어")
        self.assertEqual(items[2]["achieved"], 7)
        self.assertEqual(items[2]["target"], 7)
        self.assertAlmostEqual(items[2]["rate"], 1.0, places=4)

    def test_days_tracking(self):
        """체크된 요일이 days 리스트에 정확히 담기는지 검증."""
        items = self.calc(ROUTINE_PAGES, DATELIST)
        self.assertEqual(items[0]["days"], ["Mon", "Tue", "Wed", "Thur", "Fri"])
        self.assertEqual(items[2]["days"], DATELIST)

    def test_category_extraction(self):
        """분류 정보가 정확히 추출되는지 검증."""
        items = self.calc(ROUTINE_PAGES, DATELIST)
        self.assertEqual(items[0]["category"], "건강")
        self.assertEqual(items[1]["category"], "자기계발")

    def test_empty_title_skipped(self):
        """title이 비어있는 page는 스킵해야 한다."""
        bad_page = {"properties": {"이름": {"title": []}, "목표 개수": {"number": 7}}}
        for day in DATELIST:
            bad_page["properties"][day] = {"checkbox": False}

        items = self.calc([bad_page], DATELIST)
        self.assertEqual(len(items), 0)

    def test_missing_category(self):
        """분류(select)가 None인 경우 빈 문자열."""
        items = self.calc(MEDICINE_PAGES, DATELIST)
        self.assertEqual(items[0]["category"], "")

    def test_default_target_used_when_missing(self):
        """목표 개수가 없는 경우 default_target 사용."""
        page = {"properties": {
            "이름": {"title": [{"plain_text": "테스트"}]},
            "분류": {"select": None},
        }}
        for day in DATELIST:
            page["properties"][day] = {"checkbox": True}

        items = self.calc([page], DATELIST, default_target=5)
        self.assertEqual(items[0]["target"], 5)
        self.assertEqual(items[0]["achieved"], 7)

    def test_empty_pages(self):
        """빈 리스트 입력 시 빈 결과."""
        items = self.calc([], DATELIST)
        self.assertEqual(items, [])


class TestBuildAchievementNote(unittest.TestCase):
    """achievement_tracker.build_achievement_note 단위 테스트."""

    def setUp(self):
        from manage_notion_package.achievement_tracker import (
            calculate_per_item_achievement,
            build_achievement_note,
        )
        self.routine_items = calculate_per_item_achievement(ROUTINE_PAGES, DATELIST)
        self.medicine_items = calculate_per_item_achievement(MEDICINE_PAGES, DATELIST)
        self.build = build_achievement_note

    def test_json_structure(self):
        """JSON에 date, iso_week, routine, medicine 키가 있어야 한다."""
        note_str = self.build(self.routine_items, self.medicine_items)
        note = json.loads(note_str)

        self.assertIn("date", note)
        self.assertIn("iso_week", note)
        self.assertIn("routine", note)
        self.assertIn("medicine", note)

    def test_routine_items_in_json(self):
        """routine 항목이 name, achieved, target, rate를 포함해야 한다."""
        note = json.loads(self.build(self.routine_items, self.medicine_items))

        self.assertEqual(len(note["routine"]), 3)
        first = note["routine"][0]
        self.assertEqual(first["name"], "운동")
        self.assertEqual(first["achieved"], 5)
        self.assertEqual(first["target"], 7)
        self.assertAlmostEqual(first["rate"], 5 / 7, places=4)

    def test_medicine_items_in_json(self):
        """medicine 항목이 포함되어야 한다."""
        note = json.loads(self.build(self.routine_items, self.medicine_items))
        self.assertEqual(len(note["medicine"]), 2)
        self.assertEqual(note["medicine"][0]["name"], "비타민D")

    def test_days_excluded_from_json(self):
        """days 필드는 JSON에 포함되지 않아야 한다 (2000자 제한 대응)."""
        note = json.loads(self.build(self.routine_items, self.medicine_items))
        for item in note["routine"]:
            self.assertNotIn("days", item)

    def test_iso_week_format(self):
        """iso_week가 YYYY-Www 형식이어야 한다."""
        note = json.loads(self.build(self.routine_items, self.medicine_items))
        iso_week = note["iso_week"]
        # 형식: 2026-W07 등
        self.assertRegex(iso_week, r"^\d{4}-W\d{2}$")

    def test_under_2000_chars(self):
        """결과 JSON이 2000자를 초과하지 않아야 한다."""
        note_str = self.build(self.routine_items, self.medicine_items)
        self.assertLessEqual(len(note_str), 2000)

    def test_large_data_truncation(self):
        """항목이 매우 많을 때 2000자 제한이 적용되어야 한다."""
        many_items = [
            {"name": f"아주긴항목이름_{i}", "category": "카테고리", "achieved": i % 7,
             "target": 7, "rate": round((i % 7) / 7, 4), "days": DATELIST[:i % 7]}
            for i in range(100)
        ]
        note_str = self.build(many_items, many_items)
        self.assertLessEqual(len(note_str), 2000)

    def test_empty_items(self):
        """빈 항목으로도 유효한 JSON이 생성되어야 한다."""
        note = json.loads(self.build([], []))
        self.assertEqual(note["routine"], [])
        self.assertEqual(note["medicine"], [])


class TestUpdateAchievementRateWithNote(unittest.TestCase):
    """update_achievement_rate에서 주차, 달성률, 비고가 create_page에 올바르게 전달되는지 검증."""

    @patch("manage_notion_package.notion_api.create_page")
    @patch("manage_notion_package.notion_api.get_today_week_name", return_value="2월 셋째 주")
    def test_with_achievement_note(self, mock_week, mock_create):
        """achievement_note가 있을 때 주차 + 달성률 + 비고 3개 필드 모두 전달."""
        from manage_notion_package.achievement_tracker import (
            calculate_per_item_achievement,
            build_achievement_note,
        )
        from manage_notion_package import notion_api

        mock_create.return_value = MagicMock(status_code=200, __str__=lambda s: "<Response [200]>")

        achievement_pages = [make_achievement_page()]

        # 개별 달성률 계산
        routine_items = calculate_per_item_achievement(ROUTINE_PAGES, DATELIST)
        medicine_items = calculate_per_item_achievement(MEDICINE_PAGES, DATELIST)
        achievement_note = build_achievement_note(routine_items, medicine_items)

        # 실행
        notion_api.update_achievement_rate(achievement_pages, ROUTINE_PAGES, achievement_note)

        # create_page 호출 검증
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        data_dict = call_args[0][0]

        # 1. 주차 필드 검증
        self.assertIn("주차", data_dict["properties"])
        title_content = data_dict["properties"]["주차"]["title"][0]["text"]["content"]
        self.assertEqual(title_content, "2월 셋째 주")

        # 2. 달성률 필드 검증
        self.assertIn("달성률", data_dict["properties"])
        rate_value = data_dict["properties"]["달성률"]["number"]
        self.assertIsInstance(rate_value, float)
        self.assertGreaterEqual(rate_value, 0)
        self.assertLessEqual(rate_value, 1)

        # 3. 비고 필드 검증
        self.assertIn("비고", data_dict["properties"])
        bigo = data_dict["properties"]["비고"]
        self.assertIn("rich_text", bigo)
        note_content = bigo["rich_text"][0]["text"]["content"]

        # JSON으로 파싱 가능해야 함
        parsed = json.loads(note_content)
        self.assertIn("date", parsed)
        self.assertIn("iso_week", parsed)
        self.assertIn("routine", parsed)
        self.assertIn("medicine", parsed)

        # routine 항목 검증
        self.assertEqual(len(parsed["routine"]), 3)
        self.assertEqual(parsed["routine"][0]["name"], "운동")

        # 2000자 제한 검증
        self.assertLessEqual(len(note_content), 2000)

    @patch("manage_notion_package.notion_api.create_page")
    @patch("manage_notion_package.notion_api.get_today_week_name", return_value="2월 셋째 주")
    def test_without_achievement_note(self, mock_week, mock_create):
        """achievement_note=None일 때 비고 필드가 없어야 한다."""
        from manage_notion_package import notion_api

        mock_create.return_value = MagicMock(status_code=200, __str__=lambda s: "<Response [200]>")
        achievement_pages = [make_achievement_page()]

        notion_api.update_achievement_rate(achievement_pages, ROUTINE_PAGES, None)

        call_args = mock_create.call_args
        data_dict = call_args[0][0]

        # 주차, 달성률은 있어야 함
        self.assertIn("주차", data_dict["properties"])
        self.assertIn("달성률", data_dict["properties"])

        # 비고는 없어야 함
        self.assertNotIn("비고", data_dict["properties"])

    @patch("manage_notion_package.notion_api.create_page")
    @patch("manage_notion_package.notion_api.get_today_week_name", return_value="2월 셋째 주")
    def test_backward_compatibility(self, mock_week, mock_create):
        """기존 호출 방식(achievement_note 인자 없이)도 정상 동작해야 한다."""
        from manage_notion_package import notion_api

        mock_create.return_value = MagicMock(status_code=200, __str__=lambda s: "<Response [200]>")
        achievement_pages = [make_achievement_page()]

        # 기존 방식: 2개 인자만 전달
        notion_api.update_achievement_rate(achievement_pages, ROUTINE_PAGES)

        call_args = mock_create.call_args
        data_dict = call_args[0][0]

        self.assertIn("주차", data_dict["properties"])
        self.assertIn("달성률", data_dict["properties"])
        self.assertNotIn("비고", data_dict["properties"])


class TestFormatPerItemSection(unittest.TestCase):
    """slack.format_per_item_section 단위 테스트."""

    def setUp(self):
        from manage_notion_package.slack import format_per_item_section
        from manage_notion_package.achievement_tracker import calculate_per_item_achievement
        self.format = format_per_item_section
        self.items = calculate_per_item_achievement(ROUTINE_PAGES, DATELIST)

    def test_output_contains_title(self):
        """섹션 제목이 포함되어야 한다."""
        result = self.format(self.items, "📋 개별 루틴 현황")
        self.assertIn("📋 개별 루틴 현황", result)

    def test_output_contains_item_names(self):
        """각 항목 이름이 포함되어야 한다."""
        result = self.format(self.items)
        self.assertIn("운동", result)
        self.assertIn("독서", result)
        self.assertIn("영어", result)

    def test_output_contains_ratios(self):
        """달성 비율(n/m)이 포함되어야 한다."""
        result = self.format(self.items)
        self.assertIn("5/7", result)
        self.assertIn("3/5", result)
        self.assertIn("7/7", result)

    def test_empty_items_returns_empty(self):
        """빈 리스트는 빈 문자열을 반환해야 한다."""
        result = self.format([])
        self.assertEqual(result, "")

    def test_contains_progress_bar(self):
        """진행바 문자(█, ▓)가 포함되어야 한다."""
        result = self.format(self.items)
        self.assertTrue("█" in result or "▓" in result)


class TestWeeklyReportIntegration(unittest.TestCase):
    """create_weekly_report에 routine_items 전달 시 리포트에 개별 현황이 포함되는지 검증."""

    def setUp(self):
        from manage_notion_package.achievement_tracker import calculate_per_item_achievement
        self.routine_items = calculate_per_item_achievement(ROUTINE_PAGES, DATELIST)

    @patch("manage_notion_package.slack.get_random_advice", return_value='"테스트 명언"')
    def test_report_with_routine_items(self, mock_advice):
        """routine_items가 있으면 개별 루틴 현황이 리포트에 포함되어야 한다."""
        from manage_notion_package.slack import create_weekly_report

        report = create_weekly_report(
            achievement_rate=0.857,
            medicine_pages=MEDICINE_PAGES,
            week_name="2월 셋째 주",
            routine_items=self.routine_items,
        )

        self.assertIn("📋 개별 루틴 현황", report)
        self.assertIn("운동", report)
        self.assertIn("5/7", report)

    @patch("manage_notion_package.slack.get_random_advice", return_value='"테스트 명언"')
    def test_report_without_routine_items(self, mock_advice):
        """routine_items=None이면 개별 루틴 현황이 없어야 한다."""
        from manage_notion_package.slack import create_weekly_report

        report = create_weekly_report(
            achievement_rate=0.857,
            medicine_pages=MEDICINE_PAGES,
            week_name="2월 셋째 주",
        )

        self.assertNotIn("📋 개별 루틴 현황", report)

    @patch("manage_notion_package.slack.get_random_advice", return_value='"테스트 명언"')
    def test_report_empty_routine_items(self, mock_advice):
        """routine_items=[]이면 개별 루틴 현황이 없어야 한다."""
        from manage_notion_package.slack import create_weekly_report

        report = create_weekly_report(
            achievement_rate=0.857,
            medicine_pages=MEDICINE_PAGES,
            week_name="2월 셋째 주",
            routine_items=[],
        )

        self.assertNotIn("📋 개별 루틴 현황", report)

    @patch("manage_notion_package.slack.get_random_advice", return_value='"테스트 명언"')
    def test_no_double_blank_line_without_items(self, mock_advice):
        """routine_items가 없을 때 빈 줄이 연속 2개 이상 나오지 않아야 한다."""
        from manage_notion_package.slack import create_weekly_report

        report = create_weekly_report(
            achievement_rate=0.857,
            medicine_pages=MEDICINE_PAGES,
            week_name="2월 셋째 주",
            routine_items=[],
        )

        # "달성률 퍼센트" 줄과 "💊" 줄 사이에 빈 줄 1개만
        lines = report.split("\n")
        for i in range(len(lines) - 2):
            if "루틴 달성률" in lines[i]:
                # 진행바 줄 → 빈 줄 → 💊 줄 순서여야 함
                bar_line_idx = i + 1  # 진행바 줄
                # 빈 줄이 연속 2개 이상이면 안 됨
                blank_count = 0
                for j in range(bar_line_idx + 1, len(lines)):
                    if lines[j].strip() == "":
                        blank_count += 1
                    else:
                        break
                self.assertLessEqual(blank_count, 1,
                    f"루틴 달성률 바 이후 빈 줄이 {blank_count}개 (1개여야 함)")
                break


class TestEndToEndWorkflow(unittest.TestCase):
    """전체 워크플로우: pages → 개별달성률 → update_achievement_rate 호출까지 통합 검증."""

    @patch("manage_notion_package.notion_api.create_page")
    @patch("manage_notion_package.notion_api.get_today_week_name", return_value="2월 셋째 주")
    def test_full_workflow(self, mock_week, mock_create):
        """실제 main_with_slack의 워크플로우를 시뮬레이션."""
        from manage_notion_package import notion_api, achievement_tracker
        from manage_notion_package.achievement_tracker import (
            calculate_per_item_achievement,
            build_achievement_note,
        )

        mock_create.return_value = MagicMock(status_code=200, __str__=lambda s: "<Response [200]>")

        pages = ROUTINE_PAGES
        medicine_pages = MEDICINE_PAGES
        achievement_pages = [make_achievement_page()]

        # Step 1: 개별 달성률 계산 (main_with_slack.py line 18-21)
        routine_items = calculate_per_item_achievement(pages, DATELIST)
        medicine_items = calculate_per_item_achievement(medicine_pages, DATELIST)
        achievement_note = build_achievement_note(routine_items, medicine_items)

        # Step 2: 달성률 업데이트 (main_with_slack.py line 28)
        res = notion_api.update_achievement_rate(achievement_pages, pages, achievement_note)

        # 검증: create_page에 전달된 dict
        data_dict = mock_create.call_args[0][0]
        props = data_dict["properties"]

        # 주차
        self.assertEqual(
            props["주차"]["title"][0]["text"]["content"],
            "2월 셋째 주",
        )

        # 달성률 (3개 중 완료 여부 = all(checks[:target])인 것만)
        rate = props["달성률"]["number"]
        self.assertIsInstance(rate, float)

        # 비고
        note_json = props["비고"]["rich_text"][0]["text"]["content"]
        parsed = json.loads(note_json)

        # 루틴 3개, 약 2개
        self.assertEqual(len(parsed["routine"]), 3)
        self.assertEqual(len(parsed["medicine"]), 2)

        # 운동 5/7 검증
        exercise = next(r for r in parsed["routine"] if r["name"] == "운동")
        self.assertEqual(exercise["achieved"], 5)
        self.assertEqual(exercise["target"], 7)

        # 영어 7/7 검증
        english = next(r for r in parsed["routine"] if r["name"] == "영어")
        self.assertEqual(english["achieved"], 7)
        self.assertEqual(english["rate"], 1.0)

        # 비타민D 7/7 검증
        vitamin = next(m for m in parsed["medicine"] if m["name"] == "비타민D")
        self.assertEqual(vitamin["achieved"], 7)
        self.assertEqual(vitamin["rate"], 1.0)

    @patch("manage_notion_package.notion_api.create_page")
    @patch("manage_notion_package.notion_api.get_today_week_name", return_value="2월 셋째 주")
    def test_workflow_graceful_degradation(self, mock_week, mock_create):
        """개별 달성률 계산 실패 시에도 기존 달성률 업데이트는 정상 동작."""
        from manage_notion_package import notion_api

        mock_create.return_value = MagicMock(status_code=200, __str__=lambda s: "<Response [200]>")
        achievement_pages = [make_achievement_page()]

        # 개별 달성률 실패 시: achievement_note=None
        notion_api.update_achievement_rate(achievement_pages, ROUTINE_PAGES, None)

        data_dict = mock_create.call_args[0][0]
        props = data_dict["properties"]

        # 주차, 달성률은 정상
        self.assertIn("주차", props)
        self.assertIn("달성률", props)
        # 비고는 없음
        self.assertNotIn("비고", props)


if __name__ == "__main__":
    unittest.main()
