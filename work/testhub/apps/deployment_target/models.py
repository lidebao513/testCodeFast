"""deployment_target：合并时必须新增的基础设施（§11.3）。

testhub 当前不托管被测服务，本 app 补齐：
- 只读 git 克隆（git_url/git_token_ref/branch）
- 本地部署（run_command）+ 端口池（PortAllocation）
- 进程托管 + 探活（health_url）
"""
from django.db import models


class DeploymentTarget(models.Model):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE,
                                related_name="deploy_targets")
    git_url = models.CharField(max_length=512)
    git_token_ref = models.CharField(  # 仅存引用，明文由密钥注入解析
        max_length=255, blank=True)
    branch = models.CharField(max_length=128, default="main")
    local_path = models.CharField(max_length=512)        # 只读克隆落盘路径
    run_command = models.TextField(blank=True)           # 启动目标服务命令
    health_url = models.CharField(max_length=512, blank=True)
    base_url = models.CharField(max_length=512, blank=True)
    port = models.IntegerField(null=True, blank=True)     # 从端口池分配
    status = models.CharField(max_length=16, default="stopped",
                              choices=(("stopped", "停止"), ("running", "运行中"),
                                       ("error", "异常")))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "部署目标"

    def __str__(self):
        return f"{self.git_url}@{self.branch}"


class PortAllocation(models.Model):
    """端口池（§11.3 / settings.DEPLOY_PORT_POOL）。"""
    port = models.IntegerField(unique=True)
    occupied_by = models.ForeignKey(DeploymentTarget, null=True, blank=True,
                                    on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "端口分配"
