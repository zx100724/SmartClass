from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response


from .models import InspectionTask


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_inspection(request):
    data = request.data
    try:

        task = InspectionTask.objects.create(
            inspector=request.user,
            

            room_id=data.get('room_id'),
            classroom_id=data.get('room_id'),
            
            course_name=data.get('course_name', '未知课程'),
            teacher_name=data.get('teacher_name', '未知教师'),
            

            ai_attendance=data.get('attendance_count', 0), 
            ai_focus_rate=data.get('focus_rate', 0),

            score=data.get('rating', 5),
            tags=data.get('tags', ''),
            comment=data.get('comment', '')
        )
        return Response({"status": "success", "message": "巡课记录提交成功！"})
    
    except Exception as e:
        print(f"❌ 数据库写入失败: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_dashboard_stats(request):
    today = timezone.now().date()

    today_records = InspectionTask.objects.filter(created_at__date=today)
    

    today_count = today_records.count()
    avg_focus = today_records.aggregate(Avg('ai_focus_rate'))['ai_focus_rate__avg'] or 0
    total_student = today_records.aggregate(Sum('ai_attendance'))['ai_attendance__sum'] or 0


    score_stats = today_records.values('score').annotate(value=Count('id'))
    score_mapping = {5: '优秀', 4: '良好', 3: '一般', 2: '较差', 1: '极差'}
    pie_data = [{"value": s['value'], "name": score_mapping.get(s['score'], '未知')} for s in score_stats]


    line_data = []
    time_labels = ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00']
    for label in time_labels:
        hour = int(label.split(':')[0])
        avg_v = today_records.filter(created_at__hour=hour).aggregate(Avg('ai_focus_rate'))['ai_focus_rate__avg'] or 0
        line_data.append(round(avg_v, 1))

    return Response({
        "metrics": {
            "today_count": today_count,
            "avg_focus": round(avg_focus, 1),
            "total_student": total_student
        },
        "pie_data": pie_data,
        "line_data": line_data
    })



from rest_framework import status
from django.db.models import Q
from .models import InspectionTask 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_history_records(request):
    try:
        user = request.user
        # 获取用户组名
        group = user.groups.first()
        group_name = group.name if group else "游客"


        base_queryset = InspectionTask.objects.select_related('inspector').all().order_by('-id')

        if group_name == "管理员":
            queryset = base_queryset
        elif group_name == "巡课员":
            queryset = base_queryset.filter(inspector=user)
        else:
            return Response({"error": "权限不足：游客无权查看历史记录"}, status=status.HTTP_403_FORBIDDEN)

        # 2. 增强搜索逻辑：支持多维度模糊搜索
        keyword = request.GET.get('keyword', '').strip()
        if keyword:
            queryset = queryset.filter(
                Q(course_name__icontains=keyword) |
                Q(teacher_name__icontains=keyword) |
                Q(inspector__username__icontains=keyword) |
                Q(inspector__last_name__icontains=keyword) | 
                Q(inspector__first_name__icontains=keyword)
            )

        # 3. 数据组装
        result_data = []
        for r in queryset:
            inspector = r.inspector
            

            if inspector:
                last_name = inspector.last_name or ""
                first_name = inspector.first_name or ""
                full_name = f"{last_name}{first_name}".strip()
                display_name = full_name if full_name else inspector.username
                username = inspector.username
            else:
                display_name = "系统/已注销"
                username = "system"

            result_data.append({
                "id": r.id,
                "course_name": r.course_name,
                "teacher_name": r.teacher_name,
                "ai_attendance": r.ai_attendance,
                "ai_focus_rate": r.ai_focus_rate,
                "score": r.score,
                "tags": r.tags,
                "comment": r.comment,
                "inspector_name": display_name,     # 用于页面显示“张三”
                "inspector_username": username,     # 用于前端 v-if 判断删除权限
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
            })

        return Response({"status": "success", "data": result_data})

    except Exception as e:
        # 💡 在后端打印具体错误，方便你调试
        import traceback
        print(f"❌ 获取历史记录失败: {str(e)}")
        traceback.print_exc() 
        return Response({"error": "服务器内部错误，请联系管理员"}, status=500)


# ================= 4. 删除巡课记录 =================
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_record(request, record_id):
    try:
        record = InspectionTask.objects.get(id=record_id)
        user = request.user
        group_name = user.groups.first().name if user.groups.exists() else "游客"

        # 权限校验：管理员全删，巡课员删自己
        if group_name == "管理员" or record.inspector == user:
            record.delete()
            return Response({"status": "success", "message": "记录已删除"})
        return Response({"error": "权限不足"}, status=status.HTTP_403_FORBIDDEN)
            
    except InspectionTask.DoesNotExist:
        return Response({"error": "记录不存在"}, status=404)