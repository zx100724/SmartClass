from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

admin.site.site_header = "智慧课堂巡课系统管理后台" 
admin.site.site_title = "智慧课堂巡课系统管理后台"           


# 1. 必须先注销系统默认的 User 注册
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

from django.utils.html import format_html

@admin.register(User)
class MyUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'get_groups', 'is_active','last_login')

    def get_groups(self, obj):
        groups = [g.name for g in obj.groups.all()]
        return " | ".join(groups) if groups else "暂无分组"

    # --- 关键代码：告诉 Django 按哪个数据库字段排序 ---
    get_groups.admin_order_field = 'groups__name' 
    get_groups.short_description = '所属组'
