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


@api_view(['GET'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def facial_attendance_snapshot(request, room_id):
    """
    实时考勤快照接口
    """
    try:
        room = Classroom.objects.get(id=room_id)
        camera = getattr(room, 'camera', None)
        
        current_course = Course.objects.filter(
            classroom=room,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()

        total_count = 0
        if current_course:
            for stu_class in current_course.student_classes.all():
                total_count += stu_class.total_students
        else:
            # 💡 核心修复：移除写死的 45。
            # 如果没课，优先取教室容量，如果没有容量字段则默认为 0
            total_count = getattr(room, 'capacity', 0) 

        actual_count = 0
        if yolo_model and camera and camera.mock_image:
            results = yolo_model.predict(source=camera.mock_image.path, conf=0.3, save=False)
            for result in results:
                actual_count += len(result.boxes)
        
        attendance_rate = round((actual_count / total_count) * 100) if total_count > 0 else 0

        return Response({
            "status": "success", 
            "data": {
                "total": total_count,
                "actual": actual_count,
                "absent": max(0, total_count - actual_count),
                "ratio": attendance_rate,
                "snapshot_time": timezone.now().strftime("%H:%M:%S")
            }
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    

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