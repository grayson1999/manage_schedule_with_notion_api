### 개요

노션에서는 반복 일정을 설정할 수 있지만, 정해진 요일에 진행할 수 있도록만 도움을 준다. 

예를 들어, 월, 수, 금에 달리기를 한다고 가정하면 반복 일정 설정이 가능하지만, 1주일에 3번 달리기를 하는 목표를 설정하기 어렵다. 

따라서 이 문서에서는 주간 또는 월간 단위로 자동으로 반복 일정을 관리하도록 하는 기능을 개발하고자 한다.

### 목적

1. 반복 일정을 자동으로 관리.
2. 매주 월요일 00시에 데이터베이스를 초기화하여 한 주 일정을 다시 체크할 수 있도록 초기화.
3. 전 주 일정을 저장하여 부족한 부분을 보완하거나 잘한 점을 찾아보는 시간을 가지기 위해 데이터를 임시 저장.
4. 매 주 달성률을 저장하여 매주 또는 매달 달성률을 비교할 수 있도록 합니다.

### 기능

- 진행되는 데이터를 **현재 데이터**, 과거 저장을 위한 데이터를 **과거 데이터**로 지칭한다.

ver.1.0

1. 현재 일정이 있는 데이터베이스 자동 초기화
2. 과거 데이터 백업 및 임시 저장
    1. 과거 데이터의 일정과 현재 데이터 일정이 다를 수도 있다는 점을 파악하여 데이터베이스를 초기화 후 재 작성하는 기능을 제작.
3. 달성률 관리 데이터베이스 제작

ver.1.0.1

1. 모듈 화 및 라이브러리 제작

ver.1.0.2

1. package에 slack method 추가
2. slack method를 포함한 main_with_slack.py 추가

ver.1.0.3

1. main_with_slack.py에 오류 시 slack 메세지가 전송되도록 변경

추가 예정

1. 백업 데이터 생성 및 오류 대응
2. Slack 알림 기능
3. 약 또는 비타민 루틴 기능 추가

제한 사항

1. 한 개의 데이터베이스를 주 데이터베이스로 설정하여 일정 관리를 한다.
    1. 고유의 ID 값을 가지고 있어 이동 및 보기 복제를 통해 관리하기 용이
    2. 데이터베이스를 복사 및 삭제하여 관리할 필요가 없음
2. 데이터베이스의 이름 변경은 API로 어렵기 때문에 이름은 “이번 주”, “이전 주” 등과 같이 고정하여 사용
3. 매 주 달성률을 따로 제작한 데이터베이스에 저장
4. 단, Notion SDK - Python API로 새로운 데이터베이스를 만드는 것이 어렵기 때문에 **한 주 데이터만** 임시 저장

### Guide

Notion Page에 자신이 만든 Bot이 연결되어야 하며 권한을 부여된 상태여야 한다.

**.env**

1. NOTION_TOKEN - 노션 Secret key
2. CURRENT_DATABASE_ID  - 현재 데이터베이스 ID
3. PAST_DATABASE_ID - 한 주 데이터를 저장하기 위한 데이터베이스 ID
4. ACHIEVEMENT_DATABASE_ID - 달성률을 저장하려는 데이터베이스 ID

**run**

```python
python main.py
```

---

### 참고 자료

https://github.com/jamalex/notion-py

[How to work with the Notion API in Python - Python Engineer](https://www.python-engineer.com/posts/notion-api-python/)

[Notion API & Python](https://thienqc.notion.site/Notion-API-Python-ca0fd21bc224492b8daaf37eb06289e8)