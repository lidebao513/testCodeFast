from django.apps import AppConfig


class CodeAnalysisConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.code_analysis"
    label = "code_analysis"
    verbose_name = "代码分析（AST 功能点 + 增量溯源）"
