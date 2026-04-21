import os
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse  # 💡 添加这一行
import datetime  # 💡 添加这一行

# 💡 注意：确保你本地的 models.py 中有 InspectionRecord，如果没有请从这里删掉
from .models import Classroom, Course, Camera, StudentClass,InspectionRecord 

# ==========================================
# 1. 全局加载 YOLO 模型 (避免每次请求都重新加载)
# ==========================================
try:
    from ultralytics import YOLO
    MODEL_PATH = os.path.join(settings.BASE_DIR, 'best.pt')
    if os.path.exists(MODEL_PATH):
        yolo_model = YOLO(MODEL_PATH)
        print("YOLO模型加载成功！")
    else:
        yolo_model = None
        print("未找到 best.pt，AI接口将返回模拟数据")
except ImportError:
    yolo_model = None
    print("未安装 ultralytics，请运行 pip install ultralytics")


@api_view(['GET'])
@permission_classes([AllowAny]) 
def get_monitor_list(request):
    """
    巡课列表接口：无论摄像头在线与否，都必须返回排课信息
    """
    now = timezone.now()
    classrooms = Classroom.objects.all()
    results = []
    
    for room in classrooms:
        camera = getattr(room, 'camera', None) 
        
        video_url = None
        image_url = None
        camera_status = False

        if camera:
            camera_status = camera.status
            if camera.mock_video:
                video_url = request.build_absolute_uri(camera.mock_video.url)
            if camera.mock_image:
                image_url = request.build_absolute_uri(camera.mock_image.url)

        current_course = Course.objects.filter(
            classroom=room,
            start_time__lte=now,
            end_time__gte=now
        ).first()

        course_info = None
        if current_course:
            class_list = [str(c) for c in current_course.student_classes.all()]
            course_info = {
                "name": current_course.course_name,
                "teacher": current_course.teacher_name,
                "classes": class_list
            }

        results.append({
            "id": room.id,
            "room_name": f"{room.building}-{room.name}",
            "status": camera_status,
            "video_url": video_url,
            "image_url": image_url,
            "camera": {
                "device_id": camera.device_id if camera else "未绑定",
                "mock_video": video_url,
                "mock_image": image_url,
                "status": camera_status
            } if camera else None,
            "current_course": course_info
        })
        
    return Response({"status": "success", "data": results})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny]) 
def analyze_classroom(request, room_id):
    """
    接收教室ID，对当前摄像头画面进行 YOLO AI 行为分析
    """
    try:
        room = Classroom.objects.get(id=room_id)
        camera = getattr(room, 'camera', None)
        
        if not camera or not camera.mock_image:
            return Response({"error": "该教室暂无画面可供分析"}, status=400)

        image_path = camera.mock_image.path
        
        class_names = {
            0: 'Writing', 1: 'Reading', 2: 'Listening', 
            3: 'Turning around', 4: 'Raising hand', 
            5: 'Standing', 6: 'Discussing', 7: 'Guiding'
        }
        
        action_counts = {name: 0 for name in class_names.values()}

        if yolo_model and os.path.exists(image_path):
            results = yolo_model.predict(source=image_path, conf=0.25, save=False)
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    action_name = class_names.get(cls_id, 'Unknown')
                    if action_name in action_counts:
                        action_counts[action_name] += 1
        else:
            action_counts = {'Listening': 20, 'Reading': 15, 'Writing': 5, 'Turning around': 2}

        student_actions = ['Writing', 'Reading', 'Listening', 'Turning around', 'Raising hand', 'Standing', 'Discussing']
        total_students = sum(action_counts[action] for action in student_actions)
        if total_students == 0: total_students = 1 

        focus_count = action_counts['Listening'] + action_counts['Reading'] + action_counts['Writing'] + action_counts['Discussing']
        focus_rate = round((focus_count / total_students) * 100)

        if focus_rate >= 85: focus_level = "优秀"
        elif focus_rate >= 70: focus_level = "良好"
        elif focus_rate >= 60: focus_level = "中等"
        else: focus_level = "较差"

        warnings = []
        if action_counts['Turning around'] > 0:
            warnings.append({"icon": "🔄", "type": "交头接耳/转身", "count": action_counts['Turning around']})

        response_data = {
            "room_id": room.id,
            "total_students": total_students,
            "focus_rate": focus_rate,
            "focus_level": focus_level,
            "raw_counts": action_counts,
            "warnings": warnings
        }

        return Response({"status": "success", "data": response_data})

    except Classroom.DoesNotExist:
        return Response({"error": "教室不存在"}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": f"AI 分析失败: {str(e)}"}, status=500)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def facial_attendance_snapshot(request, room_id):
    """
    实时获取考勤快照
    """
    room = get_object_or_404(Classroom, id=room_id)
    now = timezone.now()

    # 1. 查找当前课程
    current_course = Course.objects.filter(
        classroom=room,
        start_time__lte=now,
        end_time__gte=now
    ).first()

    if not current_course:
        return JsonResponse({
            'code': 200,
            'status': 'off_schedule',
            'message': '当前非排课时间',
            'data': {'actual': 0, 'total': 0, 'absent': 0, 'ratio': 0}
        })

    # 2. 检查摄像头
    camera = getattr(room, 'camera', None)
    if not camera or not camera.status or not camera.mock_image:
        return JsonResponse({
            'code': 200,
            'status': 'offline',
            'message': '设备离线或无画面',
            'data': {'actual': 0, 'total': 0, 'absent': 0, 'ratio': 0}
        })

    # 3. 调用 YOLO 统计真实人数
    actual_count = 0
    try:
        if yolo_model and os.path.exists(camera.mock_image.path):
            results = yolo_model.predict(source=camera.mock_image.path, conf=0.25, save=False)
            
            # 💡 只要是学生的动作（0到6），全部加起来
            student_action_ids = [0, 1, 2, 3, 4, 5, 6] 
            
            for result in results:
                for box in result.boxes:
                    if int(box.cls[0].item()) in student_action_ids:
                        actual_count += 1
            
            print(f"📸 考勤抓拍成功！画面中真实识别人数为: {actual_count}")
        else:
            print("⚠️ 考勤抓拍失败：模型未加载或图片不存在")
            actual_count = 0 
    except Exception as e:
        print(f"考勤 AI 识别异常: {e}")
        actual_count = 0

    # 4. 计算结果并返回 (刚才可能就是不小心把这部分弄丢了！)
    total_count = sum(cls.total_students for cls in current_course.student_classes.all())
    absent_count = max(0, total_count - actual_count)
    attendance_ratio = round((actual_count / total_count * 100), 1) if total_count > 0 else 0

    # 💡 这个 return 至关重要，它把计算结果打包发给 Vue 前端
    return JsonResponse({
        'code': 200,
        'status': 'success',
        'data': {
            'total': total_count,
            'actual': actual_count,
            'absent': absent_count,
            'ratio': attendance_ratio,
            'course_name': current_course.course_name,
            'teacher': current_course.teacher_name
        }
    })
    

@api_view(['POST', 'GET'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def inspection_records(request):
    """
    巡课记录的保存(POST)与查询(GET)
    """
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
            return Response({"error": f"保存失败: {str(e)}"}, status=400)
    else:
        records = InspectionRecord.objects.all().order_by('-created_at')
        results = []
        for r in records:
            results.append({
                "id": r.id,
                "room": f"{r.classroom.building}-{r.classroom.name}",
                "course": r.course_name,
                "teacher": r.teacher_name,
                "attendance": r.attendance_count,
                "focus": r.focus_rate,
                "rating": r.rating,
                "tags": r.tags.split(",") if r.tags else [],
                "comment": r.comment,
                "time": r.created_at.strftime("%Y-%m-%d %H:%M")
            })
        return Response(results)