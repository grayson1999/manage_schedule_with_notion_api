import slack_sdk
import os
from dotenv import load_dotenv

load_dotenv()

SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_CHANNEL = "#notion"

def slack_message(msg):
    client = slack_sdk.WebClient(token = SLACK_TOKEN)
    client.chat_postMessage(
        channel=SLACK_CHANNEL,
        text=msg
        )
    
if __name__ == "__main__":
    text = "slack 메세지 테스트"
    slack_message(text)