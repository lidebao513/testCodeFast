# testgen-service

**代码 → 测试点 → 测试用例** 的独立生成服务。契约版本 **v1.0**。

> 定位：只负责「读懂代码并产出可交付的测试点与用例」，**不执行测试、不生成报告**。
> 与被测代码的关系：**只读**——分析完即把代码目录置只读。

---

## 快速开始

```bash
# 1) 建虚拟环境并装依赖（使用托管 Python，避免污染本机）
C:/Users/EDY/.workbuddy/binaries/python/versions/3.13.12/python.exe -m venv venv
venv/Scripts/python.exe -m pip install -r requirements.txt

# 2) 配置（可选；不配也能跑，LLM 默认关闭）
cp .env.example .env

# 3) 跑一条流水线（全量）
venv/Scripts/python.exe -m cli.main pipeline --path ../targets/research-agent

# 4) 增量（只看 git 变更）
venv/Scripts/python.exe -m cli.main pipeline --path ../targets/research-agent \
    --mode incremental --base HEAD~1 --target HEAD

# 5) 起服务
venv/Scripts/python.exe -m cli.main serve --host 127.0.0.1 --port 8100
```

## 质量门禁（一条命令，八环）

```bash
sh scripts/install_hooks.sh        # 装 git 钩子（一次性）
python scripts/gate_all.py         # 手动全量跑门禁
```

## 产出物

```
outputs/<project_id>/test_points.json    机读：测试点
outputs/<project_id>/test_cases.json     机读：用例（八要素 + 追溯键）
outputs/<project_id>/TEST_CASES.md       人读：用例清单
outputs/<project_id>/summary.json        机读：本次运行摘要
```

## HTTP 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 存活探针 |
| GET | `/ready` | 就绪探针（含脱敏配置摘要） |
| POST | `/api/v1/pipeline` | 一站式：代码 → 测试点 → 用例 |
| POST | `/api/v1/analyze` | 只做扫描 + 功能点提取 |
| GET | `/api/v1/projects` | 项目列表 |
| GET | `/api/v1/projects/{id}/test-points` | 测试点查询 |
| GET | `/api/v1/projects/{id}/cases` | 用例查询 |
| GET | `/api/v1/projects/{id}/traceability` | 追溯体检（孤儿应为 0） |
| GET | `/api/v1/workspaces` | 工作区状态 |

## 文档

- `ARCHITECTURE.md` —— 分层铁律与门禁（**开工前必读**）
- `规范文档.md` —— 规范总览与通俗说明
- 仓库根 `P1-1_契约冻结说明v1.0.md` —— 数据契约
- 仓库根 `P1-2_资产盘点表.md` —— 与 legacy 的资产对应关系
