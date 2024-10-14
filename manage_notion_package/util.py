import time
from datetime import datetime, date, timedelta, timezone
import numpy as np
import calendar
from .init import *
import json

## 에러 로그를 log 파일에 저장하는 로직
def ErrorLog(error: str):
    current_time = time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time()))
    with open("./Log.txt", "a",encoding="utf-8") as f:
        f.write(f"[{current_time}] - {error}\n")

        
## 주차 계산 로직 out: ex)9월 첫째주
def get_today_week_name():
    
    today_week_name = ""

    today = datetime.now()
    year = today.year
    month = today.month
    day = today.day

    x = np.array(calendar.monthcalendar(year, month))
    week_of_month = np.where(x == day)[0][0] + 1
    first_day_of_month = date(year, month, 1).weekday()
    flag = 0
    if first_day_of_month > 3:
        flag = 1
    week_of_month -= flag
    if week_of_month == 0:
        day_of_week = date(year, month, day).weekday()
        if day_of_week > 3:  # 목요일
            if month == 1:
                year -= 1
                month = 12
            else:
                month -= 1
            if year % 4 == 0:
                day = leap_year_last_day_of_month[month - 1]
            else:
                day = last_day_of_month[month - 1]

            x = np.array(calendar.monthcalendar(year, month))
            week_of_month = np.where(x == day)[0][0] + 1
            if date(year, month, 1).weekday() > 3:
                week_of_month -= 1
        else:
            week_of_month = 1
    elif week_of_month == 5:

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        day = 1
        day_of_week = date(year, month, day).weekday()

        if day_of_week <= 3:  # 목요일
            week_of_month = 1

    if week_of_month == 1:
        today_week_name = f"{month}월 첫째 주"
    elif week_of_month == 2:
        today_week_name = f"{month}월 둘째 주"
    elif week_of_month == 3:
        today_week_name = f"{month}월 셋째 주"
    elif week_of_month == 4:
        today_week_name = f"{month}월 넷째 주"
    elif week_of_month == 5:
        today_week_name = f"{month}월 다섯째 주"

    return today_week_name

## 오류 처리를 위한 데이터 백업 out: 백업 파일 주소
def page_backup(error_pages):
    path_backup = "./bak_page.json"
    with open(path_backup,"w", encoding="utf-8") as f:
            json.dump(error_pages,f, ensure_ascii=False)
    return path_backup