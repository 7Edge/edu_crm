from django.test import TestCase

# Create your tests here.


# from django.contrib.auth.models import AbstractUser
# from django.db import models
#
#
# class Users(AbstractUser):
#     age = models.IntegerField(verbose_name='年龄', blank=True, null=True)
#     telephone = models.CharField(verbose_name='手机号', max_length=32)
#     address = models.CharField(verbose_name='住址', max_length=255)
#
#     def __str__(self):
#         return self.username  # username属性继承自AbstractUser

from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse


@login_required
def list_customer(request):
    """
    查看用户列表
    :param request:
    :return:
    """
    pass
    return HttpResponse('用户列表')
