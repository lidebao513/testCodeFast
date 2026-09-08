"""accel_skills：平台独有核心资产（§11.3）。

testhub 全仓无 skill 概念，需原生引入：
- skill.yaml + playbook.md + helpers/ 版本化
- 复用计数 + 回流闭环（每次任务同步、新旧对比补充）
"""
from django.db import models


class Skill(models.Model):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE,
                                related_name="skills")
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    spec_path = models.CharField(max_length=512, blank=True)     # skill.yaml
    playbook_path = models.CharField(max_length=512, blank=True)  # playbook.md
    version = models.CharField(max_length=32, default="1.0.0")
    scope = models.CharField(max_length=16, default="project",
                             choices=(("project", "项目"), ("global", "全局")))
    usage_count = models.IntegerField(default=0)   # 复用计数
    created_by = models.ForeignKey("users.User", null=True, blank=True,
                                   on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("project", "name", "version")
        verbose_name = "Skill 资产"

    def __str__(self):
        return f"{self.name}@{self.version}"
