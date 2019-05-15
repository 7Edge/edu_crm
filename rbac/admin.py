from django.contrib import admin
from rbac import models


# Register your models here.


# class RbacConfig(admin.ModelAdmin):
#     list_display = [
#         'pk',
#         'p_name',
#         'url',
#         'action',
#         'group'
#     ]
#
#     list_filter = ['role', ]
#
#
# class PermissionGroupConfig(admin.ModelAdmin):
#     list_filter = ['permissions', 'title']
#
#
admin.site.register(models.PermissionGroup)
admin.site.register(models.Users)
admin.site.register(models.Role)
admin.site.register(models.Permissions)
