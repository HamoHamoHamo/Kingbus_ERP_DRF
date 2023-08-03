from django.db import models

class Member(models.Model):
    username = None
    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = []
    is_anonymous = False
    is_authenticated = True
    is_active = True

    user_id = models.CharField(max_length=100, verbose_name='사용자id', unique=True, null=True, blank=True)
    password = models.TextField(verbose_name='비밀번호', null=False, blank=True)
    name = models.CharField(verbose_name='이름', max_length=100, null=False)
    role = models.CharField(verbose_name='업무', max_length=100, null=False)
    birthdate = models.CharField(verbose_name='생년월일', max_length=100, null=False)
    phone_num = models.CharField(verbose_name='전화번호', max_length=100, null=False)
    emergency = models.CharField(verbose_name='비상연락망', max_length=100, null=False, blank=True)
    address = models.CharField(verbose_name='주소', max_length=100, null=False)
    entering_date = models.CharField(verbose_name='입사일', max_length=100, null=False)
    note = models.CharField(verbose_name='비고', max_length=100, null=False, blank=True)
    base = models.CharField(verbose_name='기본급', max_length=20, null=False, default=0)
    service_allowance = models.CharField(verbose_name='근속수당', max_length=20, null=False, default=0)
    annual_allowance = models.CharField(verbose_name='연차수당', max_length=20, null=False, default=0)
    performance_allowance = models.CharField(verbose_name='성과급', max_length=20, null=False, default=0)
    meal = models.CharField(verbose_name='식대', max_length=20, null=False, default=0)
    pub_date = models.DateTimeField(verbose_name="등록날짜", auto_now_add=True, null=False)
    creator = models.CharField(verbose_name='작성자 이름', max_length=100, null=False, blank=True)
    token = models.CharField(verbose_name='fcmtoken', max_length=100, null=False, blank=True)
    authority = models.IntegerField(verbose_name='권한', null=False, default=4)
    use = models.CharField(verbose_name='사용여부', max_length=30, null=False, default='사용')
    def __str__(self):
        return self.name
