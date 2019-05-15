#! /usr/bin/env python3
# coding:utf-8
# author:zhangjiaqi<1399622866@qq.com>
# Date:2018-10-04

"""
分页组件使用及条件：
0. 使用了 disabled 和 active 的css class 来标识 标签是否激活和禁用。和bootstrap相同，最好模版中引入bootstrap。
1. 使用render_paginator_html方法获取渲染的html，需要使用html提供<ul></ul>标签，将返回的html字符串放入该标签中（djangoform
就是这样要求的）。
2. 如果要对返回的html进行渲染，就通过对<ul class=""></ul> 来提供对其包含的<li> <a>标签进行选择渲染。
3. 如果只需要得到分页的一些结果，自己渲染，可以使用API（不断更新中）
4. 使用该分页组件，通过request.GET.get('page', 1) 来获取请求页面，用于传入API的request_page_num
5.
"""
import urllib.parse
import math


class EvenNumberForDisplayPages(Exception):
    """
    如果分页渲染标签是设置为偶数且大于等于分页总数时抛出，主要防止大于总数两边分配标签个数不均衡。
    """
    pass


class NoPageNumber(Exception):
    """
    请求的页码超出了范围
    """
    pass


class NegativeError(Exception):
    """
    分页对象总数不能为负数
    """
    pass


class NPaginator(object):
    def __init__(self, obj_cnt, per_cnt, a_tag_url='', req_get_params='', default_display_pages=5):
        if obj_cnt < 0:
            raise NegativeError('需分页对象数不能为负数！')
        self.obj_cnt = obj_cnt
        self.per_cnt = per_cnt
        self.page_num = self._calculate_page_num()
        self.a_tag_url = a_tag_url  # 需要默认为空吗？不是那么给出绝对url路径。
        self.default_display_pages = default_display_pages
        self.display_pages = self._check_display_pages()
        self.default_half_display_pages = self.default_display_pages // 2
        self.params_dict = self.urlparam2dict(req_get_params)

    @staticmethod
    def urlparam2dict(url):
        """
        将url编码字符串转换为字典
        :param url: 
        :return: 
        """
        if not url:
            return dict()
        url_param_list = url.split('&')
        temp_dict = dict()
        for url_v in url_param_list:
            kv = url_v.split('=')
            temp_dict[kv[0]] = urllib.parse.unquote(kv[1])
        return temp_dict

    def get_href(self, page_n):
        self.params_dict['page'] = page_n
        return '%s?%s' % (self.a_tag_url, urllib.parse.urlencode(self.params_dict))

    def start_point(self, req_page_num):
        req_page_num = self.validate_number(req_page_num)
        return (req_page_num - 1) * self.per_cnt

    def end_point(self, req_page_num):
        req_page_num = self.validate_number(req_page_num)
        return req_page_num * self.per_cnt

    @staticmethod
    def validate_number(number):
        """Validate the given 1-based page number."""
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise Exception('That page number is not an integer')
        if number < 1:
            raise Exception('That page number is less than 1')
        # if number > self.num_pages:
        #     if number == 1 and self.allow_empty_first_page:
        #         pass
        #     else:
        #         raise EmptyPage(_('That page contains no results'))
        return number

    def _calculate_page_num(self):
        """
        通过数据总数和每页数据量的商取天花板整数值，得到需要的总页数。如果是0则1页
        :return:
        """
        num = math.ceil(self.obj_cnt / self.per_cnt)
        if num == 0:
            num = 1
        return num

    def _check_display_pages(self):
        if self.page_num <= self.default_display_pages:
            return self.page_num
        if self.default_display_pages % 2 == 0:
            raise EvenNumberForDisplayPages('需要的分页标签显示数不能为设置偶数！')
        return self.default_display_pages

    @staticmethod
    def has_prev_page(req_page_num):
        return req_page_num > 1

    def has_next_page(self, req_page_num):
        return req_page_num < self.page_num

    def render_paginator_html(self, request_page_num=1):
        """
        返回html渲染，配套在模版文件中使用bootstrap的
        :param request_page_num:
        :return:
        """

        request_page_num = self.validate_number(request_page_num)
        curr_range = self.page_range(request_page_num)
        html_list = list()


        # 首页
        html_list.append('<li><a href="%s">首页</a></li>' % self.get_href(1))

        # 上一页
        if self.has_prev_page(request_page_num):
            prev_page = '<li><a href="%s">上一页</a></li>' % (self.get_href(request_page_num - 1))
        else:
            prev_page = '<li class="disabled"><a>上一页</a></li>'
        html_list.append(prev_page)

        # 页码标签
        for idx in curr_range:
            if idx == request_page_num:
                normal_page = '<li class="active"><a href="%s">%s</a></li>' % (self.get_href(idx), idx)
            else:
                normal_page = '<li><a href="%s">%s</a></li>' % (self.get_href(idx), idx)
            html_list.append(normal_page)

        # 下一页
        if self.has_next_page(request_page_num):
            next_page = '<li><a href="%s">下一页</a></li>' % (self.get_href(request_page_num + 1))
        else:
            next_page = '<li class="disabled"><a>下一页</a></li>'
        html_list.append(next_page)

        # 尾页
        html_list.append('<li><a href="%s">尾页</a></li>' % self.get_href(self.page_num))
        return ''.join(html_list)

    def page_range(self, request_page_num):
        """
        根据请求的页码，返回一个range对象，来表示要返回的页码范围，用于渲染。
        :param request_page_num:
        :return:
        """
        if request_page_num > self.page_num or request_page_num < 0:
            raise NoPageNumber('请求页数无效！')
        if self.default_display_pages >= self.page_num:
            return range(1, self.page_num + 1)

        # 下面是总页数self.page_num大于默认要显示的页数，就要根据请求的页数返回对应的设置的范围了
        # （三种情况：1.靠近头的；2.靠近尾的；3.中间的）
        if request_page_num <= self.default_half_display_pages + 1:  # 靠近头的
            tmp_range = range(1, self.default_display_pages + 1)
        elif request_page_num + self.default_half_display_pages >= self.page_num:  # 靠近尾的
            tmp_range = range(self.page_num + 1 - self.default_display_pages, self.page_num + 1)
        else:  # 中间的
            tmp_range = range(request_page_num - self.default_half_display_pages,
                              request_page_num + self.default_half_display_pages + 1)
        return tmp_range


if __name__ == '__main__':
    test_obj = NPaginator(20, 3, '/abc/', 'q=py&categority=20', default_display_pages=3)
    print('总页数：', test_obj.page_num)
    print(test_obj.page_range(5))
    print(test_obj.page_range(3))
    print(test_obj.page_range(1))
    print(test_obj.page_range(2))
    print(test_obj.page_range(1))
    print(test_obj.page_range(4))
    print(test_obj.render_paginator_html(2))
    print(test_obj.render_paginator_html(1))
    pass
