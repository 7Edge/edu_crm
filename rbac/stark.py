#! /usr/bin/env python3
# coding:utf-8
# author:zhangjiaqi<1399622866@qq.com>
# Date:2018-09-21
from stark.service.stark import site, ModelConfig
from rbac import models


site.register(models.Users)
site.register(models.Role)
site.register(models.Permissions)
site.register(models.PermissionGroup)


if __name__ == '__main__':
    pass
