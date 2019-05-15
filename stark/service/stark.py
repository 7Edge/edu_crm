#! /usr/bin/env python3
# coding:utf-8
# author:zhangjiaqi<1399622866@qq.com>
# Date:2018-09-22

"""
stark组件的StarkSite类 和 默认的config类：ModelConfig 类
"""
import copy
from django.urls import re_path, reverse
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.forms import ModelForm
from django.forms import ModelChoiceField
from django.db.models import Q
from django.db.models import ManyToManyField
from ..npaginator import NPaginator
import stark.configure.config as stark_configure


class RelatedField:
    pass


class NormalField:
    pass


# 将展示页面的内容封装为一个展示类里面
class QueryViewContent(object):
    def __init__(self, config_obj, request, queryset_list):
        self.config_obj = config_obj
        self.request = request
        self.queryset_list = queryset_list
        self.obj_count = self.queryset_list.count()
        self.curr_page = request.GET.get('page', 1)
        self.paginator_obj = NPaginator(self.obj_count, stark_configure.perpage_num,
                                        request.path, request.GET.urlencode(), 3)
        self.pager_html = self.paginator_obj.render_paginator_html(self.curr_page)

    def get_title_list(self):
        # 构建传给模版使用的thead数据
        t_title_list = []
        for head in self.config_obj.get_list_display():
            if callable(head):
                h_ele = mark_safe(head(self.config_obj, header=True))
            elif head == 'pk':  # 由于model是没有pk field的所以要对pk单独处理。但是'id' field是有的，这是继承过来的字段。
                h_ele = mark_safe('PK')
            elif head == '__str__':
                h_ele = mark_safe(self.config_obj.cls_model._meta.model_name.upper())
            else:
                h_ele = mark_safe(self.config_obj.cls_model._meta.get_field(head).verbose_name)
            t_title_list.append(h_ele)
        return t_title_list

    def get_data_list(self):
        # 先获取要展示的所有数据列表，由于要做过滤功能，所以后面使用的数据都是要过滤过后的数据。
        # 再用这个数据来分页来渲染。

        # 构建传给模版使用的tbody数据
        data_obj_qs = self.queryset_list[
                      self.paginator_obj.start_point(self.curr_page):self.paginator_obj.end_point(self.curr_page)]
        data_list = []
        for data_obj in data_obj_qs:
            temp_list = []
            for col in self.config_obj.get_list_display():
                if callable(col):
                    temp_list.append(col(self.config_obj, data_obj))
                else:
                    try:
                        if hasattr(data_obj, col):
                            val = getattr(data_obj, col)
                            if col == '__str__':
                                val = val()
                            elif self.config_obj.cls_model._meta.get_field(col).choices:
                                val = getattr(data_obj, 'get_' + col + '_display')()
                            # 判定不是多对多字段
                            elif isinstance(self.config_obj.cls_model._meta.get_field(col), ManyToManyField):
                                t_list = []
                                for i_obj in val.all():
                                    t_list.append(str(i_obj))
                                val = ','.join(t_list)
                            else:
                                if col in self.config_obj.list_display_link:
                                    link_url = reverse(
                                        '%s_%s_modify' % (self.config_obj.app_label, self.config_obj.model_name),
                                        args=(data_obj.pk,))
                                    val = mark_safe('<a href="%s">%s</a>' % (link_url, val))
                            temp_list.append(val)
                        else:
                            raise Exception('%s 没有 %s 字段' % (self.config_obj.cls_model._meta.model_name, col))
                    except Exception as e:
                        raise
            data_list.append(temp_list)
        return data_list

    # 处理用于渲染的 actions 批处理数据
    def get_actions_list(self):
        options_list = []
        for func_obj in self.config_obj.get_actions():
            options_list.append({'name': func_obj.__name__,
                                 'label_name': func_obj.label_name})
        return options_list

    # 给前端模版提供过滤渲染数据，数据结构形式--->[{'filter_field':field_name, 'a_tag':[<a>a tag list</a>]},...]
    def get_filter_list(self):
        temp = list()

        for field_str in self.config_obj.filter_list:
            request_get = copy.deepcopy(self.request.GET)
            if request_get.get('page'):
                del request_get['page']

            filter_dict = dict()
            filter_dict['filter_field'] = field_str
            field_obj = self.config_obj.cls_model._meta.get_field(field_str)

            a_tag_list = []
            if request_get.get(field_str):
                del request_get[field_str]
            a_tag_list.append("<a href='?%s'>%s</a>" % (request_get.urlencode(), '全部'))

            if field_obj.is_relation:  # 新的属性，用于自省对象自己。
                filter_qs = field_obj.related_model.objects.all()
                for i_obj in filter_qs:
                    request_get[field_str] = i_obj.pk
                    if str(i_obj.pk) == self.request.GET.get(field_str):
                        a_str = "<a class='active' href='?%s'>%s</a>" % (request_get.urlencode(), str(i_obj))
                    else:
                        a_str = "<a href='?%s'>%s</a>" % (request_get.urlencode(), str(i_obj))
                    a_tag_list.append(a_str)
            else:
                filter_qs = self.config_obj.cls_model.objects.all().values(field_str).distinct()
                for i_dict in filter_qs:
                    request_get[field_str] = i_dict[field_str]
                    if str(i_dict[field_str]) == self.request.GET.get(field_str):
                        a_str = "<a class='active' href='?%s'>%s</a>" % (request_get.urlencode(), i_dict[field_str])
                    else:
                        a_str = "<a href='?%s'>%s</a>" % (request_get.urlencode(), i_dict[field_str])
                    a_tag_list.append(a_str)
            filter_dict['a_tag'] = a_tag_list
            temp.append(filter_dict)

        return temp


class ModelConfig(object):
    list_display = ['__str__']
    list_display_link = []
    model_form = None
    search_fields = []
    actions = []
    filter_list = []

    def batch_delete(self, qs):
        """删除对象"""
        qs.delete()

    batch_delete.label_name = '批量删除'

    def __init__(self, model_cls, single_site):
        self.single_site = single_site
        self.cls_model = model_cls
        self.app_label = self.cls_model._meta.app_label
        self.model_name = self.cls_model._meta.model_name

        # 构建modelform

        class ModelFormDemo(ModelForm):
            class Meta:
                model = self.cls_model
                fields = '__all__'

        self.modelform = ModelFormDemo
        self.condition_value = ''

    # 定义一个方法，起到钩子的作用，但是呢？又不是一个抽象类或者接口，必须子类实现。
    # 这个方法，主要是让子类能够有自己的想法。父类这里只定义返回一个空的对象。可扩展性就提高了。

    def extra_urlparttens(self):
        return []

    # 处理modelform对象，添加css class 和 判定是否要pop
    # @staticmethod
    def do_modelform(self, form_obj):
        for bd_field in form_obj:
            bd_field.field.widget.attrs = {'class': 'form-control'}
            # if isinstance(bd_field.field, (DateField)):
            #     bd_field.field.widget.attrs = {'class': 'form-control2'}
            #     pass
            if isinstance(bd_field.field, ModelChoiceField) and bd_field.field.queryset.model._meta.app_label != 'auth':
                bd_field.is_pop = True
                rel_model = bd_field.field.queryset.model
                # 通过构建名字，反查处关联表的增加url，并且带上对应表示，最后通过该标识，作用于该标识。
                bd_field.add_url = reverse(
                    '%s:%s_%s_add' % (self.single_site.namespace,
                                      rel_model._meta.app_label,
                                      rel_model._meta.model_name)) + '?select_id=id_%s' % bd_field.name
        return form_obj

    # 整合子类和父类
    def get_actions(self):
        temp_list = list()
        temp_list.append(ModelConfig.batch_delete)
        temp_list.extend(self.actions)
        return temp_list

    # 返回需要展示的字段列表
    def get_list_display(self):
        new_list_display = []
        new_list_display.append(ModelConfig.gen_check_box)
        new_list_display.extend(self.list_display)
        new_list_display.append(ModelConfig.operations_col)
        # if not self.list_display_link:
        #     new_list_display.append(ModelConfig.gen_editor)
        # new_list_display.append(ModelConfig.gen_del)
        return new_list_display

    # 操作
    def operations_col(self, obj=None, header=False, editor=True, delete=True):
        if header:
            return '操作'
        oper_tags = []
        if editor:
            e_url = reverse('%s:%s_%s_modify' % (self.single_site.namespace, self.app_label, self.model_name), args=(obj.pk,))
            oper_tags.append(
                '<a href="%s"><span class="glyphicon glyphicon-edit" aria-hidden="true"></span></a>' % e_url)
        if delete:
            d_url = reverse('%s:%s_%s_delete' % (self.single_site.namespace, self.app_label, self.model_name), args=(obj.pk,))
            oper_tags.append(
                '<a href="%s"><span class="glyphicon glyphicon-trash" aria=hidden="true"></span></a>' % d_url)
        return mark_safe(' | '.join(oper_tags))

    # 添加编辑功能字段
    def gen_editor(self, obj=None, header=False):
        if header:
            return '编辑'
        e_url = reverse('%s:%s_%s_modify' % (self.single_site.namespace, self.app_label, self.model_name), args=(obj.pk,))
        return mark_safe('<a href="%s"><span class="glyphicon glyphicon-trash" aria-hidden="true"></span></a>' % e_url)

    # 添加删除功能字段
    def gen_del(self, obj=None, header=False):
        if header:
            return '删除'
        e_url = reverse('%s:%s_%s_delete' % (self.single_site.namespace,self.app_label, self.model_name), args=(obj.pk,))
        return mark_safe('<a href="%s"><span class="glyphicon glyphicon-edit" aria=hidden="true"></span></a>' % e_url)

    # 添加复选框功能字段
    def gen_check_box(self, obj=None, header=False):
        if header:  # 渲染为全选框
            return mark_safe('<input type="checkbox" id="all_handle">')
        return mark_safe('<input type="checkbox" name="id" value="%s">' % obj.pk)

    # 获取当前model自动生成的增删改查的url
    def get_add_url(self):
        return reverse('%s:%s_%s_add' % (self.single_site.namespace, self.app_label, self.model_name))

    def get_modify_url(self, k_id):
        return reverse('%s:%s_%s_modify' % (self.single_site.namespace, self.app_label, self.model_name), args=(k_id,))

    def get_del_url(self, k_id):
        return reverse('%s:%s_%s_delete' % (self.single_site.namespace, self.app_label, self.model_name), args=(k_id,))

    def get_query_url(self):
        return reverse('%s:%s_%s_query' % (self.single_site.namespace, self.app_label, self.model_name))

    # 获取modelform类
    def get_modelform(self):
        return self.modelform if not self.model_form else self.model_form  # 每个的初始化都会创建内，
        # 有点效率低，不应该在初始化做，因为默认的不一定都会用到。后面修改下。

    # 获取模糊查询过滤条件 Q 对象
    def get_search_q_obj(self, request):
        condition_value = request.GET.get('search', '')
        self.condition_value = condition_value
        q_obj = Q()
        if condition_value:
            q_obj.connector = 'or'
            for field in self.search_fields:
                q_obj.children.append((field + '__contains', condition_value))
        return q_obj

    # 获取filters过滤条件 Q 对象
    def get_filter_q_obj(self, request):
        q_obj = Q()
        q_obj.connector = 'and'
        for i in request.GET:
            if i not in ['page', 'search']:
                # if i in self.filter_list:
                q_obj.children.append((i, request.GET.get(i)))
        return q_obj

    # 增删改查 视图函数
    def add(self, request):
        model_form_cls = self.get_modelform()
        form = model_form_cls()
        if request.method == 'POST':
            form = model_form_cls(request.POST)
            if form.is_valid():
                new_obj = form.save()
                back_select_id = request.GET.get('select_id')
                if back_select_id:
                    return render(request, 'stark/pop.html', {'new_obj': new_obj,
                                                              'back_select_id': back_select_id})

                return redirect(to=self.get_query_url())
        # 将form 字段添加 css class 和添加is_pop属性
        form = self.do_modelform(form)

        return render(request, 'stark/add.html', {'form': form,
                                                  'model_name': self.model_name,
                                                  'operation_type': '新增'})

    def delete(self, request, k_id):
        if request.method == 'POST':
            self.cls_model.objects.filter(pk=k_id).delete()
            return redirect(to=self.get_query_url())
        return render(request, 'stark/delete_confirm.html', {'url': self.get_query_url()})
        # return HttpResponse(self.cls_model._meta.app_label + self.cls_model._meta.model_name
        #                     + '的%s id删除操作！' % k_id)

    def modify(self, request, k_id):
        m_obj = self.cls_model.objects.filter(pk=k_id).first()
        model_form_cls = self.get_modelform()
        form = model_form_cls(instance=m_obj)
        print('modify---form-->', form.is_bound)
        if request.method == 'POST':
            form = model_form_cls(request.POST, instance=m_obj)
            if form.is_valid():
                form.save()
                return redirect(to=self.get_query_url())

        form = self.do_modelform(form)

        return render(request, 'stark/modify.html', {'form': form,
                                                     'model_name': self.model_name,
                                                     'operation_type': '编辑'})

    def query(self, request):
        if request.method == 'POST':  # 查询页面的批处理流程
            action_str = request.POST.get('batch_action', '')
            if hasattr(self, action_str):
                func = getattr(self, action_str)  # 获取到绑定到对象的方法
                data_qs = self.cls_model.objects.filter(pk__in=request.POST.getlist('id'))
                func(data_qs)
            return redirect(to=self.get_query_url())

        # 先通过模糊查询逻辑，获取展示数据集
        q = self.get_search_q_obj(request)
        qs = self.cls_model.objects.filter(q)

        # 再通过过滤条件逻辑，获取展示数据集
        q_obj = self.get_filter_q_obj(request)
        n_qs = qs.filter(q_obj)

        # 实例查询展示对象
        qvc_obj = QueryViewContent(self, request, n_qs)
        # 构建传给模版使用的thead数据
        t_title_list = qvc_obj.get_title_list()
        # 构建传给模版使用的tbody数据
        data_list = qvc_obj.get_data_list()
        # 分页html字符串
        pager_html = qvc_obj.pager_html

        return render(request, 'stark/query.html', {'data_list': data_list,
                                                    't_title_list': t_title_list,
                                                    'model_name': self.model_name,
                                                    'add_url': self.get_add_url(),
                                                    'pager_html': pager_html,
                                                    'qvc_obj': qvc_obj})

    # 二次分发构建urls
    def get_url(self):
        urls_list = [re_path('^add/$', self.add, name='%s_%s_add' % (self.app_label, self.model_name)),
                     re_path('^(\d+)/delete/$', self.delete, name='%s_%s_delete' % (self.app_label, self.model_name)),
                     re_path('^(\d+)/modify/$', self.modify, name='%s_%s_modify' % (self.app_label, self.model_name)),
                     re_path('^$', self.query, name='%s_%s_query' % (self.app_label, self.model_name))]
        urls_list.extend(self.extra_urlparttens())
        return urls_list


# 单例模式 类
class StarkSite(object):
    def __init__(self):
        self._registry = {}
        self.app_label = 'stark'
        self.namespace = 'stark'

    def register(self, model_class, config_class=None):
        if not config_class:
            config_class = ModelConfig
        self._registry[model_class] = config_class(model_class, self)

    @property
    def urls(self):
        return self.get_url(), self.app_label, self.namespace

    def get_url(self):
        url_list = []
        for model_cls, config_obj in self._registry.items():  # 不要忘了modelclass和config的一一映射关联关系。
            app_label = model_cls._meta.app_label
            model_name = model_cls._meta.model_name
            url_list.append(re_path('%s/%s/' % (app_label, model_name), (config_obj.get_url(), None, None)))

        return url_list


# 单例对象
site = StarkSite()

if __name__ == '__main__':
    pass
