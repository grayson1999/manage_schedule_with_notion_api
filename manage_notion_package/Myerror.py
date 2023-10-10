class Achieve_update_error(Exception):
    def __str__(self):
        return "달성률 업데이트 중 오류가 발생했습니다."
    
class temp_raise_error(Exception):
    def __str__(self):
        return " 오류가 발생했습니다."