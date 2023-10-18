import slack_sdk
import os
from dotenv import load_dotenv
from datetime import datetime
from .init import *
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

## 초기화 전 약 먹은 달성률을 형식에 맞춰 return
#-----------------------------------------
# 약
# |Mon □ | Tue □ | Wed □ |
# |Thur □ | Fri □ | Sat □ | Sun □ |
# 달성률: | 0.0%
#-----------------------------------------
def formating_medicine_alert(medicine_pages):
    print_string = ""
    for page in medicine_pages:
        page = page["properties"]
        title = page["이름"]["title"][0]["plain_text"]
        print_string +="\n"+ title+ "\n|"
        count = 0
        check = 0
        for date in datelist:
            # □ ■
            if page[date]["checkbox"] == True:
                print_string += date+" ■ | "
                check += 1
            else:
                print_string += date+" □ | "
            count+=1
            if count == 3:
                print_string += "\n|"
        print_string+="\n"+str(check)+"회 복용\n"
    return print_string


if __name__ == "__main__":
    datetime_format = datetime.today().strftime("%Y-%m-%d %H:%M")
    text = "slack 메세지 테스트"
    slack_message("["+datetime_format+"] "+text)