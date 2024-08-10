from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from dispatch.models import  DispatchOrder
from accounting.models import TotalPrice


import re
import math

@receiver(post_save, sender=DispatchOrder)
def save_order(sender, instance, created, **kwargs):
    if instance.VAT == 'y':
        total_price = int(instance.price) * int(instance.bus_cnt)
    else:
        total_price = int(instance.price) * int(instance.bus_cnt) + math.floor(int(instance.price) * int(instance.bus_cnt) * 0.1 + 0.5)
    print("TESTTTTTTTTTTTTTT", total_price)
    if created:
        total = TotalPrice(
            order_id = instance,
            total_price = total_price,
            month = instance.departure_date[:7],
            creator = instance.creator
        )
        
    else:
        total = get_object_or_404(TotalPrice, order_id=instance)
        total.month = instance.departure_date[:7]
        total.total_price = total_price
        total.creator = instance.creator

    total.save()

    # connects는 view에서 처리
    #connects = instance.info_order.all()
    #for connect in connects:
    #    connect.price = instance.price
    #    connect.driver_allowance = instance.driver_allowance
    #    connect.save()


@receiver(pre_delete, sender=DispatchOrder)
def delete_order(sender, instance, **kwargs):
    collect_list = instance.order_collect.all()
    for collect in collect_list:
        income = collect.income_id
        income.used_price = int(income.used_price) - int(collect.price)
        if int(income.total_income) == income.used_price:
            income.state = '완료'
        else:
            income.state= '미처리'
        income.save()
        collect.delete()