import requests
import os
from dotenv import load_dotenv
from pprint import pprint
from datetime import timezone
load_dotenv()
import json
from datetime import datetime, date, timedelta
import calendar
import numpy as np
from Myerror import *
import time
import traceback


## 반복적인 일정을 관리하기 위한 notion 자동화 프로그램
## reference = https://www.python-engineer.com/posts/notion-api-python/


## 오류 내용 저장
def ErrorLog(error: str):
    current_time = time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time()))
    with open("Log.txt", "a",encoding="utf-8") as f:
        f.write(f"[{current_time}] - {error}\n")
        
## 주차 계산 로직
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

## get_database_source
def get_pages(database_id, num_pages=None):
    """
    If num_pages is None, get all pages, otherwise just the defined number.
    """
    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()

    # Comment this out to dump all data to a file
    # import json
    # with open('db.json', 'w', encoding='utf8') as f:
    #    json.dump(data, f, ensure_ascii=False, indent=4)

    results = data["results"]
    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    return results

## Creating pages in a Notion database
def create_page(data_dict,database_id):
    createUrl = 'https://api.notion.com/v1/pages'
    data_dict["parent"] = { "database_id": database_id }
    data = json.dumps(data_dict)
    res = requests.request("POST", createUrl, headers=headers, data=data)
    return res

## Updating pages in a Notion databse
def update_page(page_id: str, data: dict):
    url = f"https://api.notion.com/v1/pages/{page_id}"

    payload = {"properties": data}

    res = requests.patch(url, json=payload, headers=headers)
    return res

## Deleting pages in a Notion database
def delete_page(page_id: str):
    url = f"https://api.notion.com/v1/pages/{page_id}"

    payload = {"archived": True}

    res = requests.patch(url, json=payload, headers=headers)
    return res

## 현재 데이터를 past page의 과거 데이터로 이동
def move2pastdata(current_pages):
    ##현재 데이터를 create용 데이터 구조로 변경
    def convert_data_for_create(current_pages):
        total_convert_list = []
        for page in current_pages:
            convert_dict = {}
            for data in page["properties"].items():
                data_type = data[1]["type"]
                
                ##title 따로 분류
                if data_type == "title":
                    convert_dict[data[0]]={"title":[{"text":{"content":data[1]["title"][0]["text"]["content"]}}]}
                ##수식 page 제외
                elif data_type == 'formula':
                    pass
                ## 분류 page 따로 분류
                elif data_type == "select":
                    convert_dict[data[0]] = {data_type : {"name":data[1]["select"]["name"]}}
                ## 그 외
                else:
                    convert_dict[data[0]] = {data_type:data[1][data_type]}
            convert_dict = {
                "properties": convert_dict
            } 
            total_convert_list.append(convert_dict) 
        return total_convert_list
    
    total_convert_data_list = convert_data_for_create(current_pages)
    for data in total_convert_data_list:
        create_page(data,PAST_DATABASE_ID)

## 데이터 베이스 내 모든 데이터 삭제
def delete_all_pages(past_pages):
    ## 페이지 내 모든 id 가져오기
    for page in past_pages:
        delete_page(page["id"])

## 달성률 db에 업데이트
def update_achievement_rate(achievement_pages,current_pages):
    ## 달성률 구하기
    def calc_achevement_rate(current_pages):
   
        count = 0
        for page in current_pages:
            ##완료 여부 가져오기
            check_completed = page['properties']["완료 여부"]["formula"]['boolean']
            if check_completed:
                count += 1

        return round(count/len(pages),2)
    
    ## 달성률 UPDATE
    achievement_rate_name =""
    title_name = ""
    
    ##title 이름 가져오기
    for data in achievement_pages[0]['properties'].items():
        if data[1]['type'] == "title" or data[0] == "주차":
            title_name = data[0]
        elif data[1]['type'] == "number" or data[0] == "달성률":
            achievement_rate_name = data[0]
            
    ## properties dict로 변환
    convert_achi_dict = {
        "properties":{
            title_name : {
                "title":[{
                    "text":{
                        "content": today_week_name
                    }
                }]
            },
            achievement_rate_name:{
            "number": calc_achevement_rate(current_pages)
        }
        }
    }

    return create_page(convert_achi_dict, ACHIEVEMENT_DATABASE_ID)

## 데이터베이스 초기화(초기상태)
def reset_database(datelist,pages):
    ## 초기화용 properties 형식 만들기
    reset_properties = {}
    for date in datelist:
        reset_properties[date] = {"checkbox": False}

    ##현재 데이터 초기화
    for page in pages:
        page_id = page["id"]
        update_page(page_id,reset_properties)
        


#notion_keys
NOTION_TOKEN = auth=os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("CURRENT_DATABASE_ID")
PAST_DATABASE_ID = os.environ.get("PAST_DATABASE_ID")
ACHIEVEMENT_DATABASE_ID = os.environ.get("ACHIEVEMENT_DATABASE_ID")

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

datelist = ["Mon","Tue","Wed","Thur","Fri","Sat","Sun"]
last_day_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
leap_year_last_day_of_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
##주차 계산
today_week_name = get_today_week_name()

##페이지 가져오기
past_pages = get_pages(PAST_DATABASE_ID)
pages = get_pages(DATABASE_ID)
achievement_pages = get_pages(ACHIEVEMENT_DATABASE_ID)


if __name__ == "__main__":
    ## 달성률 업데이트
    try:
        res = update_achievement_rate(achievement_pages,pages)
        if str(res) != "<Response [200]>":
            raise Achieve_update_error

    except Exception:
        err = traceback.format_exc()
        ErrorLog(str(err))
        with open("./bak_page.json","w", encoding="utf-8") as f:
            json.dump(pages,f, ensure_ascii=False)
        ErrorLog("현재 데이터 back-up 완료 - back-up file name: bak_page.json")
        try:
            res = update_achievement_rate(achievement_pages,pages)
            if str(res) != "<Response [200]>":
                raise Achieve_update_error
        except Exception:
            err = traceback.format_exc() + "[재시도] 달성률 업데이트 중 오류 발생"
            ErrorLog(str(err))

    
    ##데이터 베이스 page 삭제
    try:
        delete_all_pages(past_pages)
    except Exception:
        err = traceback.format_exc() + "과거 데이터베이스 페이지 삭제 중 오류 발생"
        ErrorLog(str(err))
        #재시도
        try:
            delete_all_pages(past_pages)
        except Exception:
            err = traceback.format_exc() + "[재시도] 과거 데이터베이스 페이지 삭제 중 오류 발생"
            ErrorLog(str(err))
            
            
    # ##현재 데이터 과거 데이터로 옮기기
    try:
        move2pastdata(pages)
    except Exception:
        err = traceback.format_exc() + "현재 데이터 과거 테이터베이스로 옮기는 중 오류 발생"
        ErrorLog(str(err))
        
        with open("./bak_page.json","w", encoding="utf-8") as f:
            json.dump(pages,f, ensure_ascii=False)
        ErrorLog("현재 데이터 back-up 완료 - back-up file name: bak_page.json")
        
        #오류 후 백업 파일로 재시도
        try:
            delete_all_pages(past_pages)
            move2pastdata(pages)
            err = "[재시도 성공] 현재 데이터 과거 데이터베이스로 보내기 성공"
        except Exception:
            err = traceback.format_exc()+"[재시도 실패] 현재 데이터 과거 데이터베이스로 옮기는 중 오류 발생"
            
            
    # #현재 데이터 초기화
    reset_database(datelist, pages)
    
    try:
        reset_database(datelist, pages)
    except Exception:
        err = traceback.format_exc() + "현재 데이터베이스 초기화 중 오류 발생"
        ErrorLog(str(err))
        with open("./bak_page.json","w", encoding="utf-8") as f:
            json.dump(pages,f, ensure_ascii=False)
        ErrorLog("현재 데이터 back-up 완료 - back-up file name: bak_page.json")
        #재시도
        try:
            delete_all_pages(past_pages)
        except Exception:
            err = traceback.format_exc() + "[재시도] 현재 데이터베이스 초기화 중 오류 발생"
            ErrorLog(str(err))
    
    print("자동 업데이트 완료")