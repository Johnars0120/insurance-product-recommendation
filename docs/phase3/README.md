# 第三阶段开发索引

本文档用于第三阶段开发分工、分支管理、PR 提交和最终验收。第三阶段统一从 `origin/main` 开始，不再从 `codex/phase2-development` 开始。

## 当前开发基线

- GitHub 仓库：<https://github.com/Johnars0120/insurance-product-recommendation>
- 第三阶段起点：`origin/main`
- 当前确认提交：`78406b1 docs: confirm recommendation contributor credit`
- 当前总开发分支：`phase3/productization`
- 当前工作树：`.worktrees/phase3-productization`
- 基线测试：`python -m pytest -q`，结果为 `53 passed`

## 三个合并角色

| 角色 | 建议分支 | 主要任务 | PR 目标 |
| --- | --- | --- | --- |
| 页面闭环 | `phase3/ui-workflow` | 在 `/train`、`/evaluate`、`/recommend` 页面完成训练、评估、推荐、历史、导出操作闭环 | 让答辩演示不依赖 Swagger 才能操作核心流程 |
| 推荐解释 | `phase3/explain-recommendations` | 增强 `reason` 生成逻辑，提供更具体的推荐解释，并补充测试 | 让推荐结果更像业务系统输出 |
| 交付验收 | `phase3/ci-docs-demo` | 增加 GitHub Actions、第三阶段测试记录、演示流程、截图清单和 PR 检查材料 | 让项目可复现、可审查、可交付 |

这三个角色可以都由同一位开发者完成。建议仍然拆 3 个 PR，便于 GitHub 历史清晰；如果时间紧，可以在 `phase3/productization` 上连续提交后发一个总 PR。

## 开发前命令

```powershell
git fetch origin
git switch main
git pull origin main
git switch -c phase3/productization origin/main
python -m pytest -q
```

如果使用当前已创建的 worktree：

```powershell
cd "F:\工程实践II\保险产品推荐\insurance-product-recommendation\.worktrees\phase3-productization"
git status --short --branch
python -m pytest -q
```

## PR 顺序

1. 先做页面闭环，让系统具备完整浏览器演示路径。
2. 再做推荐解释，让输出结果更有说服力。
3. 最后做 CI 与文档验收，把测试记录、演示步骤和截图清单补齐。

## 每个 PR 必填内容

```text
完成内容：
修改文件：
测试命令：
测试结果：
兼容性说明：
截图或演示说明：
```

## 最终验收命令

```powershell
python -m pytest -q
git diff --check
rg -n "TB[D]|TO[DO]|待补[充]" README.md docs
```

`rg` 命令没有输出时，表示文档占位扫描通过。
