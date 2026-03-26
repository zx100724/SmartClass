
from django.contrib.auth.models import User, Group
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated


from monitor.models import InspectionRecord 


@api_view(['POST'])
@permission_classes([AllowAny]) 
def register(request):
    """处理 Vue 前端的注册请求"""
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '') 

    if not username or not password:
        return Response({'error': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': '该用户名已被注册'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(username=username, password=password, email=email)
        visitor_group = Group.objects.get(name='游客')
        user.groups.add(visitor_group)
        return Response({
            'message': '注册成功',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """获取当前登录用户的信息"""
    user = request.user
    group_name = user.groups.first().name if user.groups.exists() else "无分组"
    
    print(f"📤 [GET] 给前端发数据啦！{user.username} 的真实姓名是: '{user.first_name}'")
    
    return Response({
        'username': user.username,
        'email': user.email,
        'real_name': user.first_name, 
        'group': group_name
    })



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """处理前端修改资料（账号、姓名、邮箱）的请求"""
    user = request.user
    data = request.data
    

    print("📥 [POST] 收到前端的修改数据:", data)

    new_username = data.get('username', '').strip()
    new_email = data.get('email', '').strip()
    new_real_name = data.get('real_name', '').strip()

    if new_username and new_username != user.username:
        if User.objects.filter(username=new_username).exists():
            return Response({"error": "该用户名已被占用，请换一个"}, status=status.HTTP_400_BAD_REQUEST)
        user.username = new_username


    if 'email' in data:
        user.email = new_email
    if 'real_name' in data:
        user.first_name = new_real_name
        print("💾 [数据库操作] 准备把名字保存为:", user.first_name)
        
    user.save()
    
    return Response({
        'status': 'success',
        'message': '个人资料更新成功！',
        'new_username': user.username
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """处理修改密码逻辑"""
    user = request.user
    new_pwd = request.data.get('new_password')
    
    if not new_pwd:
        return Response({'error': '密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_pwd)
    user.save()
    
    return Response({'message': '修改成功'})


@api_view(['POST', 'GET'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def inspection_records(request):
    """旧版的巡课记录接口 (如果前端还在用这个就留着)"""
    if request.method == 'POST':
        try:
            data = request.data
            InspectionRecord.objects.create(
                classroom_id=data['room_id'],
                course_name=data['course_name'],
                teacher_name=data['teacher_name'],
                inspector="管理员", 
                attendance_count=data['attendance_count'],
                focus_rate=data['focus_rate'],
                rating=data['rating'],
                tags=",".join(data['tags']),
                comment=data['comment']
            )
            return Response({"status": "success", "message": "保存成功"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    else:
        records = InspectionRecord.objects.all().order_by('-created_at')
        res = []
        for r in records:
            res.append({
                "id": r.id,
                "room": f"{r.classroom.building}-{r.classroom.name}",
                "course": r.course_name,
                "teacher": r.teacher_name,
                "attendance": r.attendance_count,
                "focus": r.focus_rate,
                "rating": r.rating,
                "tags": r.tags.split(",") if r.tags else [],
                "comment": r.comment,
                "time": r.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(r, 'created_at') else ""
            })
        return Response(res)