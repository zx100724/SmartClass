from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny]) # 允许所有人访问注册接口
def register(request):
    """
    处理 Vue 前端的注册请求
    """
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '') # 邮箱可选

    # 1. 基础校验
    if not username or not password:
        return Response({'error': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    # 2. 检查用户是否存在
    if User.objects.filter(username=username).exists():
        return Response({'error': '该用户名已被注册'}, status=status.HTTP_400_BAD_REQUEST)

    # 3. 创建用户并保存到数据库
    try:
        user = User.objects.create_user(username=username, password=password, email=email)
        return Response({
            'message': '注册成功',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)