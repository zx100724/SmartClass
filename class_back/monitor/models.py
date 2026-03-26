from django.db import models

class StudentClass(models.Model):
    major = models.CharField(max_length=100, verbose_name="专业")
    grade = models.IntegerField(verbose_name="年级")
    class_number = models.CharField(max_length=20, verbose_name="班级编号")
    
    total_students = models.IntegerField(default=45, verbose_name="班级总人数")

    def __str__(self):
        return f"{self.grade}级{self.major}{self.class_number}班({self.total_students}人)"

    class Meta:
        verbose_name = "班级管理"
        verbose_name_plural = verbose_name

class Classroom(models.Model):
    name = models.CharField(max_length=50, verbose_name="教室名称", help_text="如：201")
    building = models.CharField(max_length=50, verbose_name="教学楼", help_text="如：明德楼")
    
    def __str__(self):
        return f"{self.building}-{self.name}"

    class Meta:
        verbose_name = "教室管理"
        verbose_name_plural = verbose_name

class Camera(models.Model):

    classroom = models.OneToOneField(
        'Classroom', 
        on_delete=models.CASCADE, 
        related_name='camera',
        null=True, blank=True,
        verbose_name="所属教室"
    )
    device_id = models.CharField(max_length=100, unique=True, verbose_name="设备ID")
    
    mock_image = models.ImageField(
        upload_to='mock/images/', 
        null=True, blank=True, 
        verbose_name="模拟图片素材"
    )
    
    mock_video = models.FileField(
        upload_to='mock/videos/', 
        null=True, blank=True, 
        verbose_name="模拟视频素材"
    )
    
    status = models.BooleanField(default=True, verbose_name="设备状态")

    def __str__(self):
        return f"摄像头({self.device_id})"
    class Meta:
        verbose_name = "监控管理"
        verbose_name_plural = "监控管理"

class Course(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='courses', verbose_name="所属教室")
    student_classes = models.ManyToManyField(StudentClass, related_name='courses', verbose_name="上课班级")
    course_name = models.CharField(max_length=100, verbose_name="课程名称")
    teacher_name = models.CharField(max_length=50, verbose_name="任课教师")
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")

    def __str__(self):
        return f"{self.course_name} - {self.teacher_name}"

    class Meta:
        verbose_name = "课程排课"
        verbose_name_plural = verbose_name


class InspectionRecord(models.Model):
    classroom = models.ForeignKey('Classroom', on_delete=models.CASCADE, verbose_name="教室")
    course_name = models.CharField(max_length=100, verbose_name="课程名称")
    teacher_name = models.CharField(max_length=50, verbose_name="任课教师")
    
    inspector = models.CharField(max_length=50, default="管理员", verbose_name="巡课员")
    attendance_count = models.IntegerField(verbose_name="实到人数")
    focus_rate = models.IntegerField(verbose_name="专注度(%)")
    
    rating = models.IntegerField(default=5, verbose_name="评分(1-5)")
    tags = models.CharField(max_length=200, blank=True, verbose_name="快捷标签")
    comment = models.TextField(blank=True, verbose_name="详细评语")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="记录时间")

    class Meta:
        verbose_name = "巡课记录"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']