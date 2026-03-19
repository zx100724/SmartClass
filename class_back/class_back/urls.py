from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView
from . import views
# 💡 别忘了导入 monitor 模块的 views，或者在下面用 include
from monitor import views as monitor_views 
from records import views as records_views
from class_back import views as class_back_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- 用户认证接口 (统一使用 class_back_views) ---
    path('api/register/', class_back_views.register, name='register'),
    path('api/login/', TokenObtainPairView.as_view(), name='login'),
    
    # 💡 个人资料维护相关的路由
    path('api/user-info/', class_back_views.get_user_info, name='user_info'),
    path('api/update-profile/', class_back_views.update_profile, name='update_profile'),
    path('api/change-password/', class_back_views.change_password),

    # --- 💡 核心业务：实时巡课接口 ---
    path('api/monitor/list/', monitor_views.get_monitor_list, name='monitor_list'),
    path('api/monitor/ai-analyze/<int:room_id>/', monitor_views.analyze_classroom, name='ai_analyze'),
    path('api/monitor/facial-attendance/<int:room_id>/', monitor_views.facial_attendance_snapshot),

    # --- 💡 历史记录与管理 ---
    path('api/records/manage/', records_views.handle_inspection),
    path('api/records/manage/<int:pk>/', records_views.handle_inspection),
    path('api/records/dashboard/', records_views.get_dashboard_stats),
    path('api/records/history/', records_views.get_history_records),
    path('api/records/history/<int:record_id>/', records_views.delete_record),
    
    # 💡 删掉了原本报错的那行 path('api/user/profile/', ...)
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)