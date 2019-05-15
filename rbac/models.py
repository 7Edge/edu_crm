from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.


class Users(AbstractUser):
    # name = models.CharField(max_length=32, verbose_name='登录用户名')
    # password = models.CharField(max_length=50, verbose_name='登录密码')
    # email = models.EmailField(verbose_name='邮箱', max_length=64)
    role = models.ManyToManyField(to='Role', verbose_name='角色')

    def __str__(self):
        return self.username


class Role(models.Model):
    title = models.CharField(max_length=32, verbose_name='角色名称')
    permission = models.ManyToManyField(to='Permissions', verbose_name='拥有权限')

    def __str__(self):
        return self.title


class Permissions(models.Model):
    p_name = models.CharField(max_length=32, verbose_name='权限名称')
    url = models.CharField(max_length=50, verbose_name='URL')
    action = models.CharField(max_length=32, verbose_name='权限操作类型')
    group = models.ForeignKey(to='PermissionGroup', to_field='id', on_delete=models.CASCADE,
                              verbose_name='权限组')

    def __str__(self):
        return self.p_name


class PermissionGroup(models.Model):
    title = models.CharField(max_length=32, verbose_name='权限组名')

    def __str__(self):
        return self.title
