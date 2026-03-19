from django.db import models
from django.contrib.auth.models import User

class InspectionTask(models.Model):
    # 1. 关联教室：引用 monitor 应用中的 Classroom 模型
    # 如果你的教室模型不在 monitor 应用下，请修改字符串前缀
    classroom = models.ForeignKey(
        'monitor.Classroom', 
        on_delete=models.CASCADE, 
        related_name='inspections',
        verbose_name="巡查教室"
    )
    
    # 2. 课程与教师信息
    course_name = models.CharField("课程名称", max_length=100, default="未知课程")
    teacher_name = models.CharField("任课教师", max_length=50, default="未知教师")
    
    # 3. AI 自动分析数据 (由前端传递或后端计算存入)
    ai_attendance = models.IntegerField("实到人数", default=0)
    ai_focus_rate = models.IntegerField("专注度(%)", default=0)
    
    # 4. 人工评价信息
    inspector_name = models.CharField("巡课员", max_length=50, default="管理员")
    score = models.IntegerField("综合评分(1-5)", default=5)
    tags = models.TextField("评价标签", blank=True, help_text="多个标签请用逗号分隔")
    comment = models.TextField("详细评语", blank=True)
    
    # 5. 时间记录
    created_at = models.DateTimeField("巡课时间", auto_now_add=True)
    updated_at = models.DateTimeField("最后修改", auto_now=True)

    # 将实到人数设置为普通整数索引，方便后续修改
    ai_attendance = models.IntegerField("实到人数(可复核)", default=0)
    
    # 也可以额外加一个备注字段，记录是否经过人工修正
    is_verified = models.BooleanField("是否已复核", default=False)

    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="巡课人")
    room_id = models.IntegerField()
    course_name = models.CharField(max_length=100)

    class Meta:
        # 这两行决定了 Django Admin 左侧菜单显示的名称
        verbose_name = "巡课历史记录"
        verbose_name_plural = "巡课历史管理"
        # 默认排序：按时间倒序排列（最新的在最上面）
        ordering = ['-created_at']

    def __str__(self):
        # 决定了在后台列表点击进去前显示的标题内容
        local_time = self.created_at.strftime("%Y-%m-%d %H:%M")
        return f"[{local_time}] {self.classroom} - {self.course_name}"