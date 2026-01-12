import logging
from logging.handlers import RotatingFileHandler
import slack_sdk
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_CHANNEL = "#notion"


class SlackHandler(logging.Handler):
    """ERROR 이상 로그를 Slack으로 전송하는 핸들러"""

    def __init__(self, token, channel):
        super().__init__()
        self.token = token
        self.channel = channel
        self.setLevel(logging.ERROR)

    def emit(self, record):
        try:
            client = slack_sdk.WebClient(token=self.token)
            log_message = self.format(record)

            datetime_format = datetime.today().strftime("%Y-%m-%d %H:%M")
            message = f"[{datetime_format}] {log_message}"

            client.chat_postMessage(
                channel=self.channel,
                text=message
            )
        except Exception:
            self.handleError(record)


def setup_logger(name="notion_scheduler"):
    """로거 설정 함수

    - 파일 핸들러: Log.txt에 모든 로그 기록 (DEBUG 이상)
    - 콘솔 핸들러: INFO 이상 출력
    - Slack 핸들러: ERROR 이상만 Slack 전송
    """
    logger = logging.getLogger(name)

    # 이미 핸들러가 설정되어 있으면 기존 로거 반환
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # 로그 포맷
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y.%m.%d/%H:%M:%S"
    )

    # 파일 핸들러 (회전 지원, 최대 5MB, 백업 3개)
    file_handler = RotatingFileHandler(
        "Log.txt",
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Slack 핸들러 (ERROR 이상)
    if SLACK_TOKEN:
        slack_handler = SlackHandler(SLACK_TOKEN, SLACK_CHANNEL)
        slack_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        logger.addHandler(slack_handler)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# 기본 로거 인스턴스
logger = setup_logger()
