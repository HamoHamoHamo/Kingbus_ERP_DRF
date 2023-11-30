from django.db import models
from humanresource.models import Member

class Client(models.Model):
    business_num = models.CharField(max_length=100, verbose_name='사업자번호', null=False, blank=True)
    name = models.CharField(max_length=100, verbose_name='거래처이름', null=False)
    representative = models.CharField(max_length=100, verbose_name='대표자명', null=False, blank=True)
    phone = models.CharField(max_length=100, verbose_name='대표전화', null=False)
    manager = models.CharField(max_length=100, verbose_name='담당자', null=False, blank=True)
    manager_phone = models.CharField(max_length=100, verbose_name='담당자번호', null=False, blank=True)
    email = models.CharField(max_length=100, verbose_name='이메일', null=False, blank=True)
    address = models.CharField(max_length=100, verbose_name='주소', null=False, blank=True)
    note = models.CharField(max_length=100, verbose_name='비고', null=False, blank=True)

    creator = models.ForeignKey(Member, on_delete=models.SET_NULL, related_name="client_user", null=True)
    pub_date = models.DateTimeField(verbose_name='작성시간', auto_now_add=True, null=False)

class Category(models.Model):
    type = models.CharField(max_length=100, verbose_name='종류', null=False)
    category = models.CharField(max_length=100, verbose_name='항목', null=False)

    creator = models.ForeignKey(Member, on_delete=models.SET_NULL, related_name="category_user", null=True)
    pub_date = models.DateTimeField(verbose_name='작성시간', auto_now_add=True, null=False)

    def __str__(self):
        return self.type + " " + self.category