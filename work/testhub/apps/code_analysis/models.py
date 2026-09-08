"""code_analysis：平台区别于 testhub"需求文档驱动"的独有价值（§11.3）。

- 静态 AST 抽取功能点（page/api/component/flow 分类）
- 关联 commit_ref，记录 change_log（新增/变更/删除 diff）
- 支撑增量重分析（git diff base..head → 功能点差异）
"""
from django.db import models


class FunctionalPoint(models.Model):
    """读代码结构得到的功能点（对齐原 functional_points 表）。"""
    FTYPE = (("api", "接口"), ("page", "页面路由"), ("component", "交互组件"),
            ("flow", "流程"))
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE,
                                 related_name="functional_points")
    commit_ref = models.CharField("关联提交", max_length=64, blank=True)
    file_path = models.CharField(max_length=512)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ftype = models.CharField(max_length=16, choices=FTYPE)
    review_status = models.CharField(  # 复用 testhub reviews 工作流
        max_length=16, default="pending",
        choices=(("pending", "待审"), ("approved", "已通过"), ("rejected", "驳回")))
    created_by = models.ForeignKey("users.User", null=True, blank=True,
                                   on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "file_path", "name", "ftype")
        verbose_name = "功能点"

    def __str__(self):
        return f"{self.ftype}:{self.name}"


class ChangeLog(models.Model):
    """增量回归溯源（对齐原 change_log 表，§11.7）。"""
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE)
    commit_from = models.CharField(max_length=64)
    commit_to = models.CharField(max_length=64)
    new_fp_ids = models.JSONField(default=list)       # 新增功能点 id
    updated_fp_ids = models.JSONField(default=list)    # 变更功能点 id
    removed_fp_ids = models.JSONField(default=list)    # 下线功能点指纹
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "变更日志"
