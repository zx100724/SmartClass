# records/admin.py
from django.contrib import admin
from .models import InspectionTask

@admin.register(InspectionTask)
class InspectionTaskAdmin(admin.ModelAdmin):
    # 1. 在列表页显示的列
    list_display = ('id', 'time_display', 'classroom', 'course_name', 'teacher_name', 'score', 'ai_attendance')
    
    # 2. 右侧筛选栏（按教室、评分、时间筛选）
    list_filter = ('classroom', 'score', 'created_at')
    
    # 3. 搜索框（支持按课程名、老师名、评语搜索）
    search_fields = ('course_name', 'teacher_name', 'comment')
    
    # 4. 每页显示多少条记录
    list_per_page = 20
    
    # 5. 只读字段（防止在后台手动修改 AI 计算的人数和专注度）
    readonly_fields = ('created_at', 'ai_attendance', 'ai_focus_rate')

    # 自定义显示时间的格式
    def time_display(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M")
    time_display.short_description = '巡课时间'