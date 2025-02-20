from manage_notion_package import notion_api,Myerror,slack,util,init
import traceback
import json
import sys
from datetime import datetime

##페이지 가져오기
past_pages = notion_api.get_pages(init.PAST_DATABASE_ID)
pages = notion_api.get_pages(init.DATABASE_ID)
achievement_pages = notion_api.get_pages(init.ACHIEVEMENT_DATABASE_ID)
medicine_pages = notion_api.get_pages(init.MEDICINE_DATABASE_ID)

if __name__ == "__main__":
    ## 달성률 업데이트
    try:
        res = notion_api.update_achievement_rate(achievement_pages,pages)
        if str(res) != "<Response [200]>":
            raise Myerror.Achieve_update_error

    except Exception:
        err = traceback.format_exc()
        util.ErrorLog(str(err))
        slack.slack_message_with_time("달성률 업데이트 중 오류가 발생했습니다.\n프로그램을 종료합니다.")
        ##프로그램 종료
        sys.exit()
    
    
    ##과거 데이터 베이스 DB 초기화(내부 page 전체 삭제)
    try:
        res = notion_api.delete_all_pages(past_pages)
    except Exception:
        err = traceback.format_exc()
        util.ErrorLog(str(err))
        slack.slack_message_with_time("과거 데이터베이스 초기화 중 오류가 발생했습니다.\n프로그램을 종료합니다.")
        ##프로그램 종료
        sys.exit()
            
            
    ##현재 데이터 과거 데이터로 옮기기
    try:
        res = notion_api.move2pastdata(pages)

    except Exception:
        err = traceback.format_exc()
        util.ErrorLog(str(err))
        slack.slack_message_with_time("현재 데이터를 과거 데이터로 옮기는 중 오류가 발생했습니다.\n프로그램을 종료합니다.")
        ##프로그램 종료
        sys.exit()
            
            
    ##현재 데이터 초기화
    try:
        res = notion_api.reset_database(init.datelist, pages)       
    except Exception:
        err = traceback.format_exc() 
        util.ErrorLog(str(err))
        slack.slack_message_with_time("현재 데이터베이스 초기화 중 오류가 발생했습니다.\n프로그램을 종료합니다.")
        ##프로그램 종료
        sys.exit()
    
    slack.slack_message_with_time(
        "\n이번주 " + str(notion_api.ACHEVEMENT_RATE * 100) + "% 달성하였습니다.")
        
    ##약 루틴 초기화
    notion_api.reset_database(init.datelist,medicine_pages)
    slack.slack_message(
        "\n"+slack.formating_medicine_alert(medicine_pages)+"약 루틴 초기화를 완료했습니다.\n"
        )
    
    ##완료 메시지
    slack.slack_message(
        "notion 일정이 정상 초기화 되었습니다."
    )