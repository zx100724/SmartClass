from django.contrib import admin
from django.utils.html import format_html
from .models import Classroom, Camera, StudentClass, Course

# 修改后台管理界面标题
admin.site.site_header = "智慧课堂巡课系统后台"
admin.site.index_title = "监控与排课业务管理"


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'status', 'preview_mock')
    
    def preview_mock(self, obj):

        if obj.mock_video:
            return format_html(
                '<a href="{}" target="_blank" style="background: #409EFF; color: white; padding: 2px 6px; border-radius: 4px; text-decoration: none;">🎬 播放视频</a>', 
                obj.mock_video.url
            )
        elif obj.mock_image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 35px; object-fit: cover; border-radius: 2px; border: 1px solid #eee;" />', 
                obj.mock_image.url
            )
        return "无素材"
    
    preview_mock.short_description = "画面预览"

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'building')
    list_filter = ('building',)
    search_fields = ('name', 'building')


@admin.register(StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = ('grade', 'major', 'class_number', 'display_full_name')
    list_filter = ('grade', 'major')

    def display_full_name(self, obj):
        return f"{obj.grade}级{obj.major}{obj.class_number}班"
    display_full_name.short_description = "班级全名"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):

    list_display = ('course_name', 'teacher_name', 'classroom', 'start_time', 'end_time')
    list_filter = ('classroom', 'teacher_name')
    search_fields = ('course_name', 'teacher_name')
    

    filter_horizontal = ('student_classes',) 
    

    date_hierarchy = 'start_time'