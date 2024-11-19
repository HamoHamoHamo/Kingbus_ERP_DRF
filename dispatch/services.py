from .models import DispatchOrderConnect, DispatchRegularlyConnect, ConnectStatus
from .serializers import DailyDispatchRegularlyConnectListSerializer, DailyDispatchOrderConnectListSerializer

# 복잡한 비즈니스 로직 처리, 간단한건 ModelSerializer로 처리
class DispatchRegularlyConnectService:
    @staticmethod
    def get_locations(connect_id: int) -> str:
        try:
            connect = DispatchRegularlyConnect.objects.get(id=connect_id)
            return connect.locations
        except DispatchRegularlyConnect.DoesNotExist:
            raise ValueError(f"connect ID {connect_id}를 찾을 수 없습니다.")
        except Exception as e:
            raise Exception(f"locations 조회 중 오류 발생: {str(e)}")


class DispatchConnectService:
    # 현재 해야하는 배차 정보 불러오기
    @staticmethod
    def get_current_connect(connects):
        """
        운행 완료가 아닌 가장 첫 번째 배차를 찾습니다.
        
        Args:
            connects (list): 배차 정보가 담긴 리스트
            
        Returns:
            dict or None: 조건에 맞는 첫 번째 배차. 없으면 None 반환
        """
        
        for connect in connects:            
            # 상태가 '운행 완료'가 아닌 첫번째 배차정보 리턴
            if connect['status'] != ConnectStatus.COMPLETE:
                return connect
                
        return None 

    # 배차 데이터 불러오기
    @staticmethod
    def get_daily_connect_list(date, user):
        regularly_connects = DispatchRegularlyConnect.objects.filter(departure_date__startswith=date, driver_id=user).select_related('regularly_id', 'bus_id')
        order_connects = DispatchOrderConnect.objects.filter(departure_date__startswith=date, driver_id=user).select_related('order_id', 'bus_id')

        return regularly_connects, order_connects
        