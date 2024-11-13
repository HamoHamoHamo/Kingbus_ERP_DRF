from .models import DispatchRegularlyConnect


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


