from django.apps import AppConfig


class DeploymentTargetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.deployment_target"
    label = "deployment_target"
    verbose_name = "被测目标部署（只读克隆+端口池+托管+探活）"
