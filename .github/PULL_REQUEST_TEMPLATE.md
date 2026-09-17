## 变更说明
<!-- 简述本次 PR 的目的与范围，关联哪个子项目（testgen-service / test-accel） -->

## 关联
- 关联任务 / 议题（如有）：

## 自检清单（合并前必过）
- [ ] 本地已跑对应子项目门禁全绿（testgen：`python work/testgen-service/scripts/gate_all.py`；test-accel：`python work/test-accel/scripts/gate_all.py`）
- [ ] 提交信息遵循 Conventional Commits（如 `feat(testgen): ...` / `fix(...)` / `chore(...)`）
- [ ] 未提交任何密钥 / 凭据（`.env`、`*.pem`、`*.key`、明文 token、`tokens.json` 等已在 .gitignore）
- [ ] 测试通过（门禁内的 pytest）

## 测试计划
<!-- 如何验证本次变更；若涉及运行时 UI / 真实 LLM，说明是否已在可达网络环境验证 -->
