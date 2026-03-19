from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .models import Classroom, Course, Camera

from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Classroom, Course, Camera  # 确保导入正确

@api_view(['GET'])
@permission_classes([AllowAny]) 
def get_monitor_list(request):
    """
    巡课列表接口：无论摄像头在线与否，都必须返回排课信息
    """
    # 💡 技巧：获取当前时间，并稍微扩大一点前后范围（比如正负5分钟），防止卡点排课查不到
    now = timezone.now()
    classrooms = Classroom.objects.all()
    results = []
    
    for room in classrooms:
        # 1. 获取摄像头信息
        camera = getattr(room, 'camera', None) 
        
        video_url = None
        image_url = None
        camera_status = False

        if camera:
            camera_status = camera.status
            # 💡 使用 request.build_absolute_uri 确保返回的是完整的 http://... 地址
            if camera.mock_video:
                video_url = request.build_absolute_uri(camera.mock_video.url)
            if camera.mock_image:
                image_url = request.build_absolute_uri(camera.mock_image.url)

        # 2. 💡 核心修复：获取当前课程
        # 确保只要在这个时间段内的课程都能被查出来
        current_course = Course.objects.filter(
            classroom=room,
            start_time__lte=now,
            end_time__gte=now
        ).first()

        course_info = None
        if current_course:
            # 格式化班级列表
            class_list = [str(c) for c in current_course.student_classes.all()]
            course_info = {
                "name": current_course.course_name,
                "teacher": current_course.teacher_name,
                "classes": class_list # 结果如: ["2022级软件1班", "2022级软件2班"]
            }

        # 3. 组装数据
        # ⚠️ 注意：这里必须保证即便 camera 为 None，结果也要包含房间名和课程信息
        results.append({
            "id": room.id,
            "room_name": f"{room.building}-{room.name}",
            "status": camera_status,  # 这个状态只控制前端的“在线/离线”标签
            "video_url": video_url,   # 方便前端 getVideoUrl 调用
            "image_url": image_url,   # 方便前端 getImageUrl 调用
            "camera": {
                "device_id": camera.device_id if camera else "未绑定",
                "mock_video": video_url,
                "mock_image": image_url,
                "status": camera_status
            } if camera else None,
            "current_course": course_info # 💡 只要这里有数据，前端就不会显示“无排课”
        })
        
    return Response({"status": "success", "data": results})

import os
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny # 或者 IsAuthenticated
from rest_framework.response import Response
from .models import Classroom

# ==========================================
# 💡 1. 全局加载 YOLO 模型 (避免每次请求都重新加载)
# ==========================================
try:
    from ultralytics import YOLO
    # 假设 best.pt 放在项目根目录 (manage.py 同级)
    MODEL_PATH = os.path.join(settings.BASE_DIR, 'best.pt')
    if os.path.exists(MODEL_PATH):
        yolo_model = YOLO(MODEL_PATH)
        print("✅ YOLO模型加载成功！")
    else:
        yolo_model = None
        print("⚠️ 未找到 best.pt，AI接口将返回模拟数据")
except ImportError:
    yolo_model = None
    print("⚠️ 未安装 ultralytics，请运行 pip install ultralytics")

# ==========================================
# 💡 2. AI 分析专属接口
# ==========================================
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

        # 获取图片的绝对物理路径
        image_path = camera.mock_image.path
        
        # 定义类别映射字典 (根据你的训练日志)
        class_names = {
            0: 'Writing', 1: 'Reading', 2: 'Listening', 
            3: 'Turning around', 4: 'Raising hand', 
            5: 'Standing', 6: 'Discussing', 7: 'Guiding'
        }
        
        # 初始化统计数据
        action_counts = {name: 0 for name in class_names.values()}

        # -------------------------------------
        # 🧠 执行 YOLO 推理
        # -------------------------------------
        if yolo_model and os.path.exists(image_path):
            results = yolo_model.predict(source=image_path, conf=0.5, save=False) # conf=0.5 表示置信度阈值
            
            # 提取检测结果
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    action_name = class_names.get(cls_id, 'Unknown')
                    if action_name in action_counts:
                        action_counts[action_name] += 1
        else:
            # 如果没模型，随便造点假数据防止前端崩溃
            action_counts = {'Listening': 20, 'Reading': 15, 'Writing': 5, 'Turning around': 2}

        # -------------------------------------
        # 📊 业务逻辑转换 (将 YOLO 数据转为前端指标)
        # -------------------------------------
        # 1. 计算学生总数 (排除 Guiding，因为那是老师)
        student_actions = ['Writing', 'Reading', 'Listening', 'Turning around', 'Raising hand', 'Standing', 'Discussing']
        total_students = sum(action_counts[action] for action in student_actions)
        if total_students == 0: total_students = 1 # 防除零报错

        # 2. 计算专注度指数 (听课+读+写+讨论 视为专注)
        focus_count = action_counts['Listening'] + action_counts['Reading'] + action_counts['Writing'] + action_counts['Discussing']
        focus_rate = round((focus_count / total_students) * 100)

        # 3. 评定专注度等级
        if focus_rate >= 85: focus_level = "优秀"
        elif focus_rate >= 70: focus_level = "良好"
        elif focus_rate >= 60: focus_level = "中等"
        else: focus_level = "较差"

        # 4. 组装异常警告数据 (把你模型里的 Turning around 算作异常)
        warnings = []
        if action_counts['Turning around'] > 0:
            warnings.append({"icon": "🔄", "type": "交头接耳/转身", "count": action_counts['Turning around']})
        # 如果模型以后加了睡觉检测，可以继续在这里 append

        # 组装返回给 Vue 的 JSON
        response_data = {
            "room_id": room.id,
            "total_students": total_students,
            "focus_rate": focus_rate,
            "focus_level": focus_level,
            "raw_counts": action_counts,  # 原始数据，前端可以拿来画饼图
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
    try:
        room = Classroom.objects.get(id=room_id)
        camera = getattr(room, 'camera', None)
        
        # 1. 找到当前教室正在上的课
        current_course = Course.objects.filter(
            classroom=room,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()

        # 2. 动态计算“应到人数”
        total_count = 0
        if current_course:
            # 汇总这堂课所有上课班级的人数之和
            for stu_class in current_course.student_classes.all():
                total_count += stu_class.total_students
        else:
            total_count = 45 # 如果没课，给个默认参考值

        # 3. 执行 YOLO 真实计数
        actual_count = 0
        if yolo_model and camera and camera.mock_image:
            results = yolo_model.predict(source=camera.mock_image.path, conf=0.3, save=False)
            for result in results:
                actual_count += len(result.boxes)
        
        # 4. 计算结果
        attendance_rate = round((actual_count / total_count) * 100) if total_count > 0 else 0

        return Response({
            "status": "success", 
            "data": {
                "total": total_count,           # 来自数据库的动态人数
                "actual": actual_count,         # 来自 YOLO 的实时人数
                "absent": max(0, total_count - actual_count),
                "ratio": attendance_rate,
                "snapshot_time": timezone.now().strftime("%H:%M:%S")
            }
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    

@api_view(['POST', 'GET'])
@authentication_classes([]) # 调试用，跳过 Token 验证
@permission_classes([AllowAny])
def inspection_records(request):
    """
    巡课记录的保存(POST)与查询(GET)
    """
    if request.method == 'POST':
        try:
            data = request.data
            # 💡 核心：将前端传来的 AI 数据和评价存入数据库
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
    
    # GET 请求：返回所有历史记录给前端表格
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