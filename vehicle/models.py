from django.db import models
from humanresource.models import Member
from datetime import datetime
from uuid import uuid4

class Vehicle(models.Model):
    vehicle_num0 = models.CharField(verbose_name='차량번호 앞자리', max_length=15, null=False)
    vehicle_num = models.CharField(verbose_name='차량번호', max_length=15, null=False)
    vehicle_id = models.CharField(verbose_name='차대번호', max_length=30, null=False, blank=True)
    motor_type = models.CharField(verbose_name='원동기형식', max_length=30, null=False, blank=True)
    rated_output = models.CharField(verbose_name='정격출력', max_length=15, null=False, blank=True)
    vehicle_type = models.CharField(verbose_name='차량이름', max_length=50, null=False, blank=True)
    maker = models.CharField(verbose_name='제조사', max_length=50, null=False, blank=True)
    model_year = models.CharField(verbose_name='연식', max_length=15, null=False, blank=True)
    release_date = models.CharField(verbose_name='출고일자', max_length=15, null=False, blank=True)
    driver = models.OneToOneField(Member, verbose_name='기사', on_delete=models.SET_NULL, null=True, related_name="vehicle", db_column="vehicle")
    driver_name = models.CharField(verbose_name='기사이름', max_length=20, null=False, blank=True)
    use = models.CharField(verbose_name='사용여부', max_length=10, null=False, default='사용', blank=True)
    passenger_num = models.CharField(verbose_name='승차인원', max_length=100, null=False, blank=True)

    check_date = models.CharField(verbose_name='정기점검일', max_length=30, null=False, blank=True)
    type = models.CharField(verbose_name='형식', max_length=50, null=False, blank=True)
    creator = models.ForeignKey(Member, on_delete=models.SET_NULL, related_name="vehicle_user", db_column="user_id", null=True)
    pub_date = models.DateTimeField(verbose_name='작성시간', auto_now_add=True, null=False)
    
    def __str__(self):
        return f'{self.id} / {self.vehicle_num}'