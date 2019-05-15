from django.db import models
# from rbac.models import Users
from django.conf import settings


# Create your models here.

class Department(models.Model):
    """
    部门表
    """
    title = models.CharField(verbose_name='部门名称', max_length=32)
    code = models.IntegerField(verbose_name='部门编号', unique=True, null=False)

    def __str__(self):
        return self.title


class UserInfo(models.Model):
    """
    员工表
    """
    name = models.CharField(verbose_name='员工姓名', max_length=32)
    # username = models.CharField(verbose_name='用户名', max_length=32)
    # password = models.CharField(verbose_name='登录密码', max_length=64)
    # email = models.EmailField(verbose_name='邮箱', max_length=64)
    age = models.IntegerField(verbose_name='年龄')

    depart = models.ForeignKey(verbose_name='部门', to='Department', to_field='code', on_delete=models.CASCADE)
    rbac_user = models.OneToOneField(verbose_name='登录用户', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, )

    def __str__(self):
        return self.name


class Course(models.Model):
    """
    课程表
    如：
        Linux基础
        Linux架构师
        Python自动化开发精英班
        Python自动化开发架构师班
        Python基础班
        Go基础班
    """
    name = models.CharField(verbose_name='课程名称', max_length=32)

    def __str__(self):
        return self.name


class School(models.Model):
    """
    校区表
    如：
        北京校区
        上海校区
        深圳校区
        成都校区
    """
    name = models.CharField(verbose_name='校区名称', max_length=16)

    def __str__(self):
        return self.name


class ClassList(models.Model):
    """
    班级表
    """
    school = models.ForeignKey(verbose_name='校区', to='School', to_field='id', on_delete=models.CASCADE)
    course = models.ForeignKey(verbose_name='课程', to='Course', to_field='id', on_delete=models.CASCADE)

    semester = models.IntegerField(verbose_name='班级(期)')
    price = models.DecimalField(verbose_name='价格', max_digits=10, decimal_places=2)
    start_date = models.DateField(verbose_name='开班日期')
    graduate_date = models.DateField(verbose_name='毕业日期', blank=True, null=True)
    memo = models.CharField(verbose_name='说明', max_length=200, blank=True)

    teachers = models.ManyToManyField(verbose_name='任课老师', to='UserInfo', related_name='classlist_teacher',
                                      limit_choices_to={'depart__in': [1002, 1005]})
    tutor = models.ForeignKey(verbose_name='班主任', to='UserInfo', to_field='id', on_delete=models.CASCADE,
                              related_name='classlist_tutor', limit_choices_to={'depart': 1001})

    def __str__(self):
        return '{0}({1}期)'.format(self.course.name, self.semester)


class Customer(models.Model):
    """
    客户表
    """
    qq = models.CharField(verbose_name='QQ', max_length=32, unique=True, help_text='QQ号必须唯一')

    name = models.CharField(verbose_name='客户姓名', max_length=15)
    gender_choices = ((1, '男'),
                      (2, '女'))
    gender = models.SmallIntegerField(verbose_name='性别', choices=gender_choices, )

    education_choices = ((1, '重点大学'),
                         (2, '普通本科'),
                         (3, '独立院校'),
                         (4, '民办本科'),
                         (5, '大专'),
                         (6, '民办专科'),
                         (7, '高中'),
                         (8, '其它'))
    education = models.SmallIntegerField(verbose_name='学历', choices=education_choices, blank=True, null=True)
    graduation_school = models.CharField(verbose_name='毕业院校', max_length=64, blank=True, null=True)
    major = models.CharField(verbose_name='专业', max_length=32, blank=True, null=True)

    experience_choices = ((1, '在校生'),
                          (2, '应届毕业'),
                          (3, '半年以内'),
                          (4, '半年至一年'),
                          (5, '一年至三年'),
                          (6, '三年至五年'),
                          (7, '五年以上'),)
    experience = models.SmallIntegerField(verbose_name='工作经验', choices=experience_choices, blank=True, null=True)
    work_status_choices = ((1, '在职'),
                           (2, '无业'))
    work_status = models.SmallIntegerField(verbose_name='职业状态', choices=work_status_choices, blank=True, null=True)
    company = models.CharField(verbose_name='目前就职公司', max_length=32, blank=True, null=True)
    salary = models.DecimalField(verbose_name='当前薪资', max_digits=10, decimal_places=2, blank=True, null=True)
    source_choices = [
        (1, "qq群"),
        (2, "内部转介绍"),
        (3, "官方网站"),
        (4, "百度推广"),
        (5, "360推广"),
        (6, "搜狗推广"),
        (7, "腾讯课堂"),
        (8, "广点通"),
        (9, "高校宣讲"),
        (10, "渠道代理"),
        (11, "51cto"),
        (12, "智汇推"),
        (13, "网盟"),
        (14, "DSP"),
        (15, "SEO"),
        (16, "其它"),
    ]
    source_choices = models.IntegerField(verbose_name='客户来源', choices=source_choices, default=1)
    referral_from = models.ForeignKey(verbose_name='转介绍自学员', to='self', to_field='id', blank=True, null=True,
                                      help_text='若此客户是转介绍自内部学员,请在此处选择内部学员姓',
                                      on_delete=models.CASCADE)
    purpose_course = models.ManyToManyField(verbose_name='咨询课程', to='Course', blank=True, )
    status_choices = ((1, "已报名"),
                      (2, "未报名"))
    status = models.SmallIntegerField(verbose_name='状态', choices=status_choices, default=2,
                                      help_text="选择客户此时的状态")
    consultant = models.ForeignKey(verbose_name='咨询顾问', to='UserInfo', to_field='id',
                                   limit_choices_to={'depart': 1001}, on_delete=models.CASCADE)
    date = models.DateField(verbose_name='咨询日期', auto_now_add=True)
    recv_date = models.DateField(verbose_name='接单日期', null=True)
    last_consult_date = models.DateField(verbose_name='最后更近日期')

    def __str__(self):
        return '姓名:{0},QQ:{1}'.format(self.name, self.qq)


class MyCustomers(models.Model):
    """
    我的咨询客户表（包括成单，跟进，未成单等）
    """
    consultant = models.ForeignKey(verbose_name='咨询顾问', to='UserInfo', to_field='id', on_delete=models.CASCADE,
                                   limit_choices_to={'depart': 1001})
    customer = models.ForeignKey(verbose_name='客户', to='Customer', to_field='id', on_delete=models.CASCADE)
    date = models.DateField(verbose_name='日期')
    state_choices = ((1, '成单'),
                     (2, '跟进'),
                     (3, '3天未跟进'),
                     (4, '15天未成单'),)
    state = models.SmallIntegerField(verbose_name='客户状态', choices=state_choices, )
    memo = models.CharField(verbose_name='备注', max_length=255)

    def __str__(self):
        return '%s %s %s' % (self.consultant, self.get_state_display(), self.customer)


class ConsultRecord(models.Model):
    """
    客户跟进记录
    """
    customer = models.ForeignKey(verbose_name='咨询客户', to='Customer', to_field='id', on_delete=models.CASCADE)
    consultant = models.ForeignKey(verbose_name='跟踪人', to='UserInfo', on_delete=models.CASCADE,
                                   limit_choices_to={'depart': 1001})
    date = models.DateField(verbose_name='跟进记录日期', auto_now_add=True)
    note = models.TextField(verbose_name='跟进内容')

    def __str__(self):
        return self.customer.name + ':' + self.consultant.name


class Student(models.Model):
    """
    学生表
    """
    customer = models.OneToOneField(verbose_name='客户信息', to='Customer', on_delete=models.CASCADE)

    username = models.CharField(verbose_name='用户名', max_length=32)
    password = models.CharField(verbose_name='登录密码', max_length=64)
    emergency_contract = models.CharField(verbose_name='紧急联系人', max_length=64, blank=True)

    class_list = models.ManyToManyField(verbose_name='已报班级', to='ClassList', blank=True)

    company = models.CharField(verbose_name='公司', max_length=128, blank=True, null=True)
    location = models.CharField(max_length=64, verbose_name='所在区域', blank=True, null=True)
    position = models.CharField(verbose_name='岗位', max_length=64, blank=True, null=True)
    salary = models.IntegerField(verbose_name='薪资', blank=True, null=True)
    welfare = models.CharField(verbose_name='福利', max_length=256, blank=True, null=True)

    date = models.DateField(verbose_name='入职时间', help_text='格式yyyy-mm-dd', blank=True, null=True)
    memo = models.CharField(verbose_name='备注', max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username


class CourseRecord(models.Model):
    """
    上课纪录
    """
    class_obj = models.ForeignKey(verbose_name='班级', to='ClassList', on_delete=models.CASCADE)

    day_num = models.IntegerField(verbose_name='节次', help_text='此处填写第几节课或第几天课程...,必须为数字')
    teacher = models.ForeignKey(verbose_name='上课老师', to='UserInfo', on_delete=models.CASCADE,
                                limit_choices_to={'depart__in': [1002, 1003]})
    date = models.DateField(verbose_name='上课日期', auto_now_add=True)
    course_title = models.CharField(verbose_name='本节课标题', max_length=64, blank=True, null=True)
    course_memo = models.TextField(verbose_name='本节课程内容概要', blank=True, null=True)
    has_homework = models.BooleanField(verbose_name='本节有作业', default=True)
    homework_title = models.CharField(verbose_name='本节作业标题', max_length=64, blank=True, null=True)
    homework_memo = models.TextField(verbose_name='作业描述', max_length=500, blank=True, null=True)
    exam = models.TextField(verbose_name='踩分点', max_length=300, blank=True, null=True)

    def __str__(self):
        return '{0} day{1}'.format(self.class_obj, self.day_num)


class StudyRecord(models.Model):
    course_record = models.ForeignKey(verbose_name='第几天课程', to='CourseRecord', on_delete=models.CASCADE)
    student = models.ForeignKey(verbose_name='上课学生', to='Student', on_delete=models.CASCADE)
    record_choices = (('checked', "已签到"),
                      ('vacate', "请假"),
                      ('late', "迟到"),
                      ('noshow', "缺勤"),
                      ('leave_early', "早退"),
                      )
    record = models.CharField(verbose_name='上课记录', choices=record_choices, default='checked', max_length=32)
    score_choices = ((100, 'A+'),
                     (90, 'A'),
                     (85, 'B+'),
                     (80, 'B'),
                     (70, 'B-'),
                     (60, 'C+'),
                     (50, 'C'),
                     (40, 'C-'),
                     (0, ' D'),
                     (-1, 'N/A'),
                     (-100, 'COPY'),
                     (-1000, 'FAIL'),
                     )
    score = models.IntegerField(verbose_name='本节成绩', choices=score_choices, default=-1)
    homework_note = models.CharField(verbose_name='作业评语', max_length=255, blank=True, null=True)
    note = models.CharField(verbose_name='备注', max_length=255, blank=True, null=True)

    homework = models.FileField(verbose_name='作业文件', blank=True, null=True, default=None)
    stu_memo = models.TextField(verbose_name='学生备注', blank=True, null=True)
    date = models.DateTimeField(verbose_name='提交作业时间', auto_now_add=True)

    def __str__(self):
        return "{0}-{1}".format(self.course_record, self.student)