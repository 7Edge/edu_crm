#! /usr/bin/env python3
# coding:utf-8
# author:zhangjiaqi<1399622866@qq.com>
# Date:2018-11-14

"""
提供初始化权限，放入session会话中。
"""
from .. import models


def init_permissons(request, user):
    """
    将用户的权限结构化为{1:{'urls':[], 'actions':[]},}形式，并存入到会话中。
    :param request:
    :param user:
    :return:
    """
    p_list = models.Permissions.objects.filter(role__users=user).values('url',
                                                                        'action',
                                                                        'group').distinct()
    # 转换数据结构
    data = {}
    for item in p_list:
        group = item['group']
        if group not in data:
            data[group] = {}
            data[group]['urls'] = [item['url']]
            data[group]['actions'] = [item['action']]
        else:
            data[group]['urls'].append(item['url'])
            data[group]['actions'].append(item['actions'])
    request.session['permission_dict'] = data


if __name__ == '__main__':
    pass
