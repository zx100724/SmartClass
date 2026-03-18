from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # 注册接口：由我们刚才写的 views.register 处理
    path('api/register/', views.register, name='register'),
    
    # 登录接口：直接使用 SimpleJWT 提供的视图，它会自动验证并返回 Token
    path('api/login/', TokenObtainPairView.as_view(), name='login'),

]