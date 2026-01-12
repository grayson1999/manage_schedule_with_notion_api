from manage_notion_package import notion_api,Myerror,slack,util,init
from manage_notion_package.logger import logger
import traceback
import sys
from datetime import datetime

##페이지 가져오기
past_pages = notion_api.get_pages(init.PAST_DATABASE_ID)
pages = notion_api.get_pages(init.DATABASE_ID)
achievement_pages = notion_api.get_pages(init.ACHIEVEMENT_DATABASE_ID)


if __name__ == "__main__":
    ## 달성률 업데이트
    try:
        res = notion_api.update_achievement_rate(achievement_pages,pages)
        if str(res) != "<Response [200]>":
            raise Myerror.Achieve_update_error

    except Exception:
        err = traceback.format_exc()
        logger.error(f"달성률 업데이트 중 오류가 발생했습니다.\n{err}")
        sys.exit()


    ##데이터 베이스 page 삭제
    try:
        res = notion_api.delete_all_pages(past_pages)
    except Exception:
        err = traceback.format_exc()
        logger.error(f"과거 데이터베이스 초기화 중 오류가 발생했습니다.\n{err}")
        sys.exit()


    ##현재 데이터 과거 데이터로 옮기기
    try:
        res = notion_api.move2pastdata(pages)

    except Exception:
        err = traceback.format_exc()
        logger.error(f"현재 데이터를 과거 데이터로 옮기는 중 오류가 발생했습니다.\n{err}")
        sys.exit()


    ##현재 데이터 초기화
    try:
        res = notion_api.reset_database(init.datelist, pages)
    except Exception:
        err = traceback.format_exc()
        logger.error(f"현재 데이터베이스 초기화 중 오류가 발생했습니다.\n{err}")
        sys.exit()


