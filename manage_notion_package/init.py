import os
from dotenv import load_dotenv
load_dotenv()

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
