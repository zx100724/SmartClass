import os
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

# 💡 注意：确保你本地的 models.py 中有 InspectionRecord，如果没有请从这里删掉
from .models import Classroom, Course, Camera, InspectionRecord 

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
            results = yolo_model.predict(source=image_path, conf=0.5, save=False)
            
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


def facial_attendance_snapshot(request, room_id):
    """
    实时获取考勤快照。
    逻辑：检查当前教室、当前时间是否有排课，若无则返回 off_schedule。
    """
    room = get_object_or_404(Classroom, id=room_id)
    
    # 获取当前时间与星期
    now = datetime.datetime.now()
    current_time = now.time()
    day_of_week = now.weekday() + 1  # Django 中通常 1-7 代表周一到周日

    # 1. 查找当前教室在该时间段的课程
    current_schedule = StudentClass.objects.filter(
        room=room,
        day_of_week=day_of_week,
        start_time__lte=current_time,
        end_time__gte=current_time
    ).first()

    # 💡 核心修改：如果没有排课，直接返回“非授课时间”状态
    if not current_schedule:
        return JsonResponse({
            'code': 200,
            'status': 'off_schedule',
            'message': '当前非排课时间',
            'data': {
                'actual': 0,
                'total': 0,
                'absent': 0,
                'ratio': 0
            }
        })

    # 2. 如果有排课，则进行正常的考勤逻辑（此处为示例，需结合你的识别逻辑）
    # 假设你从 Camera 获取实时画面并调用 YOLO
    actual_count = 0 
    try:
        # 这里放置你的识别逻辑
        # actual_count = perform_yolo_detection(room.camera)
        actual_count = 25  # 模拟识别到的人数
    except Exception as e:
        print(f"AI 识别异常: {e}")

    total_count = current_schedule.total_students or 0
    absent_count = max(0, total_count - actual_count)
    attendance_ratio = round((actual_count / total_count * 100), 1) if total_count > 0 else 0

    return JsonResponse({
        'code': 200,
        'status': 'success',
        'data': {
            'total': total_count,
            'actual': actual_count,
            'absent': absent_count,
            'ratio': attendance_ratio,
            'course_name': current_schedule.name,
            'teacher': current_schedule.teacher
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