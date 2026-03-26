from django.urls import path
from monitor import views as monitor_views

urlpatterns = [

    path('api/monitor/list/', monitor_views.get_monitor_list, name='monitor_list'),
    
    path('api/monitor/ai-analyze/<int:room_id>/', monitor_views.analyze_classroom, name='ai_analyze'),
]