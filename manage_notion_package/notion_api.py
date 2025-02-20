import json
import requests 
from .init import *
from .util import get_today_week_name

ACHEVEMENT_RATE = 0
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
            # Assuming '완료 여부' is a property containing a formula that evaluates to boolean
            check_completed = page['properties'].get("완료 여부", {}).get("formula", {}).get('boolean', False)
            if check_completed:
                count += 1

        # Calculate percentage achievement rate
        if len(current_pages) > 0:
            achievement_rate = round(count / len(current_pages), 4)
        else:
            achievement_rate = 0

        return achievement_rate
        
    global ACHEVEMENT_RATE 
    ACHEVEMENT_RATE = calc_achevement_rate(current_pages)
    
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
                        "content": get_today_week_name()
                    }
                }]
            },
            achievement_rate_name:{
            "number": ACHEVEMENT_RATE
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


