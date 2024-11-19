from rest_framework import serializers
from datetime import datetime
from common.constant import DATE_FORMAT

class TimeFormatValidator:
    def __call__(self, value):
        try:
            # 문자열을 시간 객체로 변환 시도
            time = datetime.strptime(value, '%H:%M').time()
            
            # 00:00 ~ 23:59 범위 체크는 자동으로 됨
            # (strptime이 이 범위를 벗어나면 ValueError를 발생시킴)
            return value
        except ValueError:
            raise serializers.ValidationError("Time must be in format HH:MM (00:00-23:59)")


class DateFormatValidator:
    def __call__(self, value):
        try:
            # 문자열을 날짜 객체로 변환 시도
            datetime.strptime(value, DATE_FORMAT)
            return value
        except ValueError:
            raise serializers.ValidationError("Invalid date format")
