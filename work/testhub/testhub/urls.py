"""testhub 根路由。合并后各 app 通过 DRF router 挂载。"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # 复用 testhub 既有 API
    path("api/projects/", include("apps.projects.urls")),
    path("api/testcases/", include("apps.testcases.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/ai/", include("apps.requirement_analysis.urls")),
    path("api/executions/", include("apps.executions.urls")),
    # === 合并"测试加速平台"新增能力（§11.3）===
    path("api/code-analysis/", include("apps.code_analysis.urls")),
    path("api/accel-skills/", include("apps.accel_skills.urls")),
    path("api/deploy/", include("apps.deployment_target.urls")),
]
