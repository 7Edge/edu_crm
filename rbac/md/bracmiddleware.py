#! /usr/bin/env python3
# coding:utf-8
# author:zhangjiaqi<1399622866@qq.com>
# Date:2018-09-07

"""
中间件：
访问权限鉴别；
清洗出当前访问权限的同组权限操作权限列表，并将清洗的列表保存到当前会话保存中。
"""
import re
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import HttpResponse
from ..configure import rbac_config


class RbacMiddle(MiddlewareMixin):
    """
    权限中间件：用于过滤当前用户登录用户的权限；白名单权限访问则放过；
    """

    def process_request(self, request):
        req_url = request.path_info
        # 白名单放过
        white_permission_list = rbac_config.white_url_list
        for w_url in white_permission_list:
            w_url = '^%s$' % w_url
            if re.match(w_url, req_url):
                return None  # 白名单放过

        # print(white_permission_list)

        # 检测非白名单权限匹配情况，即当前会话登录用户的权限。
        # 权限数据存在会话中的‘permission_dict’ key中。权限结构是一个{1:{'urls':[], 'actions':[]},}字典；
        # 之所以使用该数据结构而不直接使用一个url列表，是由于要进行数据清洗，获取同组权限操作列表。
        # 数据结构决定了算法解决了麻烦的方式；最初方式就是url列表；
        check_permission_dict = request.session.get('permission_dict')

        if check_permission_dict:
            for item in check_permission_dict:
                for c_url in check_permission_dict[item]['urls']:
                    c_url = '^%s$' % c_url
                    if re.match(c_url, req_url):
                        # 如果匹配到权限，即可以访问，然后将和该权限同组的权限放入 数据载体对象httprequest中。
                        # 因为权限不仅涉及到检测，还有同类权限的界面UI接口渲染（或者说权限粒度如果有父子树关系，那么就要考虑当前访问权限应该渲染出来的UI
                        # 是否有子url需要在当前url页面中渲染；一般来说都是有的，所以可以将这些权限在数据库的权限组表中表示分类出来。这样就可以按照分组的方式
                        # 存储到会话session中；就像这里用到的一个字典，字典的key就是权限分组的pk。这样既能判断权限，也能方便反查处所处同一页面的url列表，
                        # 从而进行渲染。）。
                        # 所以中间件不止有校验权限；还有提供给view函数渲染权限UI的基础数据。
                        request['actions'] = check_permission_dict[item]['actions']
                        return None

        return HttpResponse('没权访问！')


if __name__ == '__main__':
    pass
