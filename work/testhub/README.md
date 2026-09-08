# testhub（合并目标平台）

本目录是"测试加速平台"（源自 `work/test-accel`，FastAPI/SQLite/原生 HTML）**合并进 testhub** 的目标工程脚手架。

> 合并不是复制粘贴，而是把平台能力落到 testhub 既有的 Django app 体系。完整方案见设计文档 §11 / §12，以及本目录内的：

- **[MIGRATION.md](./MIGRATION.md)** — 详细迁移文档（环境要求 / 项目结构 / 分步执行命令 / 验证清单）
- **[TASK_PLAN.md](./TASK_PLAN.md)** — 后续任务计划（未完成任务的目标 / 范围 / 在 testhub 中的执行顺序）

## 技术栈（既定，合并阶段对齐）
- 后端：Django 4.2 + DRF；ASGI 走 Daphne(:8000) + Channels
- 任务：Celery（worker + beat）；缓存/ broker：Redis
- 存储：MySQL 8.0 默认，支持 `DB_ENGINE=sqlite3` 平迁
- 前端：Vue3 + Vite + Element Plus + vue-i18n（zh/en/ja/ko），:3000

## 目录结构（与 §11 对齐）
```
testhub/
├── manage.py
├── testhub/                 # Django 项目包（settings/urls/asgi/wsgi）
├── apps/
│   ├── code_analysis/       # 新建① AST 功能点 + change_log（§11.3）
│   ├── accel_skills/        # 新建② Skill 资产库（§11.3）
│   ├── deployment_target/   # 新建③ 只读克隆+端口池+托管+探活（§11.3）
│   ├── projects/ testcases/ reports/ reviews/ requirement_analysis/
│   ├── ui_automation/ executions/ core/ users/   # 复用 testhub 既有
│   └── monitor/             # 探活复用（§12.5）
├── frontend/                # Vue3（src/views|api|store|router|locales）
├── requirements.txt
├── .env.example
├── start_dev.sh
├── MIGRATION.md
└── TASK_PLAN.md
```
