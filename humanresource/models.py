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
    interview_date = models.CharField(verbose_name='면접일', max_length=100, null=False, blank=True)
    contract_date = models.CharField(verbose_name='계약일', max_length=100, null=False, blank=True)
    contract_renewal_date = models.CharField(verbose_name='근로계약갱신일', max_length=100, null=False, blank=True)
    contract_condition = models.CharField(verbose_name='근로계약조건', max_length=100, null=False, blank=True)
    renewal_reason = models.CharField(verbose_name='갱신사유', max_length=100, null=False, blank=True)
    apply_path = models.CharField(verbose_name='지원경로', max_length=100, null=False, blank=True)
    career = models.CharField(verbose_name='경력사항', max_length=100, null=False, blank=True)
    position = models.CharField(verbose_name='직급', max_length=100, null=False, blank=True)
    apprenticeship_note = models.CharField(verbose_name='견습노선 및 내용', max_length=100, null=False, blank=True)
    leave_reason = models.CharField(verbose_name='퇴사사유', max_length=100, null=False, blank=True)

    base = models.CharField(verbose_name='기본급', max_length=20, null=False, default=0)
    service_allowance = models.CharField(verbose_name='근속수당', max_length=20, null=False, default=0)
    annual_allowance = models.CharField(verbose_name='연차수당', max_length=20, null=False, default=0)
    performance_allowance = models.CharField(verbose_name='성과급', max_length=20, null=False, default=0)
    meal = models.CharField(verbose_name='식대', max_length=20, null=False, default=0)
    
    pub_date = models.DateTimeField(verbose_name="등록날짜", auto_now_add=True, null=False)
    creator = models.CharField(verbose_name='작성자 이름', max_length=100, null=False, blank=True)
    token = models.CharField(verbose_name='fcmtoken', max_length=500, null=False, blank=True)
    authority = models.IntegerField(verbose_name='권한', null=False, default=4)
    use = models.CharField(verbose_name='사용여부', max_length=30, null=False, default='사용')
    def __str__(self):
        return self.name
