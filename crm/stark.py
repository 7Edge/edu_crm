#! /usr/bin/env python3
# coding:utf-8
# author:zhangjiaqi<1399622866@qq.com>
# Date:2018-11-07

"""

"""
import datetime
from django.db.models import Q
from django.db import transaction
from django.urls import re_path, reverse
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from django.forms import ModelForm, widgets
from stark.service.stark import site
from stark.service.stark import ModelConfig
from crm.models import *

site.register(Department)


class UserInfoConfig(ModelConfig):
    # 展示字段
    list_display = ['name', 'username', 'email', 'age', 'depart']
    # 指定字段用于连接编辑
    list_display_link = ['name']

    # 自定义modelform
    class UserInfoModelForm(ModelForm):
        class Meta:
            model = UserInfo
            fields = '__all__'
            widgets = {'password': widgets.PasswordInput}

    model_form = UserInfoModelForm


site.register(UserInfo, UserInfoConfig)
site.register(Course)
site.register(School)


class ClassListConfig(ModelConfig):
    # 将course字段和semester字段合在一起展示
    def class_semester(self, obj=None, header=False):
        if header:
            return '班级名称'
        return '%s(%s)期' % (obj.course, obj.semester)

    list_display = [class_semester, 'tutor', 'teachers']


site.register(ClassList, ClassListConfig)


class CustomerConfig(ModelConfig):
    # 性别展示
    def display_gender(self, obj=None, header=False):
        if header:
            return '性别'
        return obj.get_gender_display()

    # 咨询课程字段
    def display_purpose_course(self, obj=None, header=False):
        if header:
            return '咨询课程'
        obj_list = obj.purpose_course.all()
        tags_list = []
        for j_obj in obj_list:
            c_url = reverse('%s:cancel_cus_2_course' % self.single_site.namespace, args=[obj.id, j_obj.id])
            a_tag = '<a href="%s" style="border: 1px solid #369; padding: 3px 6px;">%s</a>&nbsp;' % (c_url, str(j_obj))
            tags_list.append(a_tag)
        return mark_safe(' '.join(tags_list))

    list_display = ['name', display_gender, 'consultant', display_purpose_course, 'status', 'recv_date',
                    'last_consult_date']

    def cancel_purpose_course(self, request, cus_id, cou_id):
        customer_obj = self.cls_model.objects.get(id=cus_id)
        customer_obj.purpose_course.remove(cou_id)
        return redirect(self.get_query_url())

    def public_customer(self, request):
        curr_date = datetime.datetime.now()
        delta_3day = datetime.timedelta(days=3)
        delta_15day = datetime.timedelta(days=15)
        pub_customers = Customer.objects.filter(
            Q(recv_date__lt=curr_date - delta_15day) | Q(last_consult_date__lt=curr_date - delta_3day), status=2)
        return render(request, 'crm/public_customer.html', {'pub_customers': pub_customers})

    def obtain_customer(self, request, c_id):
        curr_loign_user = '7'

        now = datetime.datetime.now()
        delta_3day = datetime.timedelta(days=3)
        delta_15day = datetime.timedelta(days=15)
        # 更新和创建要在一个事务中
        try:
            with transaction.atomic():
                ret = Customer.objects.filter(
                    Q(recv_date__lt=now - delta_15day) | Q(last_consult_date__lt=now - delta_3day),
                    id=c_id).update(consultant=curr_loign_user, last_consult_date=now,
                                    recv_date=now)
                if not ret:
                    return HttpResponse('跟进失败！客户已被跟进！')
                MyCustomers.objects.create(consultant_id=curr_loign_user, customer_id=c_id, date=now, state=2)
                return HttpResponse('跟进成功！')
        except Exception as e:
            raise e

    def my_customers(self, request):
        curr_login_user = '7'
        my_c_objs = MyCustomers.objects.filter(consultant=curr_login_user)
        return render(request, 'crm/my_customers.html', {'my_c_objs': my_c_objs})

    # 扩展url的钩子
    def extra_urlparttens(self):
        url_list = []
        url_list.append(re_path('^cancel_purpose/(\d+)/(\d+)/', self.cancel_purpose_course, name='cancel_cus_2_course'))
        url_list.append(re_path('^public_customers/', self.public_customer, name='public_customers'))
        url_list.append(re_path('^obtain_customer/(\d+)/', self.obtain_customer, name='obtain_customer'))
        url_list.append(re_path('^my_customers/', self.my_customers, name='my_customers'))
        return url_list


site.register(Customer, CustomerConfig)


class ConsultRecordConfig(ModelConfig):
    list_display = ['customer', 'consultant', 'date', 'note']


site.register(ConsultRecord, ConsultRecordConfig)


class StudentConfig(ModelConfig):
    # 添加一个跳转学生详细页，或者说学生主页的字段
    def go_std_detail(self, obj=None, header=False):
        if header:
            return "学生详情"
        return mark_safe(
            "<a href='%s'>学习情况</a>" % reverse('%s:study_detail' % self.single_site.namespace, args=(obj.id,)))

    list_display = ['customer', 'class_list', go_std_detail]
    list_display_link = ['customer']

    # 扩展url，学生学习详情页
    def extra_urlparttens(self):
        obj_url = re_path('^studydetail/(\d+)/', self.study_record, name='study_detail')
        return [obj_url]

    # 学习详情页view函数(后面引入分页)
    def study_record(self, request, std_id):
        if request.is_ajax():
            study_qs = StudyRecord.objects.filter(course_record__class_obj=request.GET.get('cls'),
                                                  student=request.GET.get('std'))
            chart_data = []
            for s_obj in study_qs:
                chart_data.append([s_obj.course_record.day_num, s_obj.score])
            return JsonResponse(chart_data, safe=False)
        cls_list = ClassList.objects.filter(student__pk=std_id)
        temp_dict = {}
        for cls_obj in cls_list:
            std_r_list = StudyRecord.objects.filter(student=std_id, course_record__class_obj=cls_obj)
            temp_dict[cls_obj.pk] = std_r_list
        return render(request, 'crm/study_detail.html', {'data': temp_dict,
                                                         'std_id': std_id})


site.register(Student, StudentConfig)


class CourseRecordConfig(ModelConfig):
    # 查看本节课的上课记录
    def goto_study_record(self, obj=None, header=False):
        if header:
            return '学生上课记录'
        return mark_safe("<a href='%s?course_record=%s'>记录</a>" % ('/stark/crm/studyrecord/', obj.id))

    # 录入成绩
    def do_score(self, obj=None, header=False):
        if header:
            return "录入成绩"
        return mark_safe(
            "<a href='%s'>录成绩</a>" % (reverse('%s:enter_course_score' % self.single_site.namespace, args=[obj.id])))

    list_display = ['class_obj', 'day_num', 'teacher', 'course_title', goto_study_record, do_score]

    # 定义一个action 批处理动作
    def batch_std_record(self, qs):
        """
        批量在StudyRecord表中添加本堂课班级学生的上课记录
        :param qs:
        :return:
        """
        for cb_obj in qs:
            std_qs = cb_obj.class_obj.student_set.all()
            std_re_list = []
            for std_obj in std_qs:
                std_re_list.append(StudyRecord(course_record=cb_obj, student=std_obj))
            StudyRecord.objects.bulk_create(std_re_list)

    batch_std_record.label_name = '对课程添加批量上课纪录'

    actions = [batch_std_record]

    # 扩展录入成绩view 函数
    def enter_score(self, request, cou_id):
        if request.method == 'POST':
            update_data = {}
            for k, v in request.POST.items():
                if k == 'csrfmiddlewaretoken': continue

                f_name, obj_id = k.rsplit('_', 1)

                if obj_id in update_data:
                    update_data[obj_id][f_name] = v
                else:
                    update_data[obj_id] = {f_name: v}

            for obj_pk, d_data in update_data.items():
                StudyRecord.objects.filter(id=obj_pk).update(**d_data)
            return redirect(to=request.path)

        cou_obj = CourseRecord.objects.get(id=cou_id)
        sr_qs_list = StudyRecord.objects.filter(course_record=cou_id)
        score_choices = StudyRecord.score_choices
        return render(request, 'crm/enter_score.html', {'sr_qs_list': sr_qs_list,
                                                        'cou_obj': cou_obj,
                                                        'score_choices': score_choices})

    def extra_urlparttens(self):
        url_obj = re_path('^enterscore/(\d+)/', self.enter_score, name='enter_course_score')
        return [url_obj]


site.register(CourseRecord, CourseRecordConfig)


class StudyRecordConfig(ModelConfig):

    def display_score(self, obj=None, header=False):
        if header:
            return "分数"
        return obj.get_score_display()

    def display_record(self, obj=None, header=False):
        if header:
            return "上课记录"
        return obj.get_record_display()

    # list_display = ['course_record', 'student', display_record, display_score]
    list_display = ['course_record', 'student', 'record', display_score]
    filter_list = ['course_record']

    # 迟到处理
    def batch_late(self, qs):
        qs.update(record='late')

    batch_late.label_name = '迟到处理'
    actions = [batch_late]


site.register(StudyRecord, StudyRecordConfig)

if __name__ == '__main__':
    pass
