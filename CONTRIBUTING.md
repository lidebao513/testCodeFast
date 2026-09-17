# 贡献约定（testCodeFast）

> 本文档是仓库级治理红线，配合 `.github/workflows/ci.yml`（远程门禁）与
> `.pre-commit-config.yaml`（本地门禁）共同生效。

## 1. 分支模型
- **`main`**：受保护主干。只接受「通过 PR + CI 门禁」的合并，禁止直接 push。
- **功能分支**：`dev/<主题>` 或 `feat/<议题>`。本地开发在此进行，验证（八环门禁全绿）后
  fast-forward 合并进 `main`。
- **两条代码线**：
  - `work/testgen-service/` —— 用例生成主引擎（唯一活跃线）。
  - `work/test-accel/` —— 历史兼容线，仅维护、不再主开发。

## 2. 提交信息约定（Conventional Commits，本地 pre-commit 强制）
格式：`type(scope): 简述`（英文小写 type，中文简述亦可）
- `type`：`feat` / `fix` / `chore` / `docs` / `refactor` / `test` / `perf` / `ci`
- `scope`（可选）：`testgen` / `test-accel` / `security` / `ci` …
- 示例：
  - `feat(testgen): 新增对话代理模板渲染`
  - `fix(test-accel): 修正增量基线校验空引用`
  - `chore(security): 解耦 tokens.json 取消跟踪并加入 .gitignore`

不符格式会被 `commit-msg` 钩子拒绝。

## 3. PR 流程
1. 从功能分支向 `main` 提 PR。
2. 描述使用 `.github/PULL_REQUEST_TEMPLATE.md` 模板。
3. CI（八环门禁）必须全绿；合并前勾选自检清单。
4. 合并方式：fast-forward / squash，保持线性历史。

## 4. 密钥与凭据（红线）
- **严禁提交任何密钥 / 凭据**：`.env`、`*.pem`、`*.key`、明文 token、`tokens.json`、
  含账号密码的配置文件等。
- 上述类型已在 `.gitignore` 屏蔽；`tokens.json` 已取消跟踪（见提交 `14a81c6`）。
- 提交前自查：
  ```bash
  git diff --cached --name-only | grep -iE "\.env$|venv/|\.db$|token"
  ```
- 若历史提交误含凭据：
  1. **先在源系统轮换对应凭据**（根本消解泄露风险）；
  2. 再评估是否用 `git filter-repo` 重写历史（**破坏性操作**，会改写已推送的共享历史，
     需团队明确同意并协调重克隆，切勿单方面强推）。

## 5. CI（远程门禁）
见 `.github/workflows/ci.yml`：push / PR 到 `main` 时，分别在 GitHub runner 上跑
`work/testgen-service` 与 `work/test-accel` 的八环门禁（含 secret scan / ruff / mypy /
bandit / pytest 覆盖率）。CI 全绿是合并 `main` 的前置条件。

## 6. `main` 分支保护（需在 GitHub 网页设置，本机 `gh` 未安装）
仓库 **Settings → Branches → Add rule**（Branch name pattern 填 `main`）：
- ☑ Require a pull request before merging
- ☑ Require status checks to pass before merging
  - 勾选 CI 的两个 job：`testgen-service 八环门禁`、`test-accel 质量门禁`
- ☑ Require branches to be up to date before merging
- ☑ Do not allow bypassing the above rules
- （建议）☑ Include administrators

> 在 CI 首次于 GitHub runner 跑通并确认稳定前，先不要勾选「Require status checks」，
> 避免把尚未调优的 CI 变成合并阻塞。
