# Phase 3 Productization Design

## Goal

第三阶段把现有保险产品智能推荐系统从“接口能力完整”推进到“浏览器页面可完整演示、推荐结果可解释、交付流程可复现”的产品化版本。开发基线固定为 `origin/main` 的 `78406b1`，不再从 `codex/phase2-development` 或旧 Phase 1 工作树继续开发。

## Current Baseline

- Phase 2 已合并到 GitHub `main`。
- 当前稳定能力包括 SQLite 持久化、多模型训练与对比、ECharts 图表、推荐历史、CSV 导出和 53 个自动化测试。
- 最后一次记录的基线验证为 `python -m pytest -q`，结果 `53 passed`。
- 当前 Phase 3 工作树为 `.worktrees/phase3-productization`，分支为 `phase3/productization`，跟踪 `origin/main`。

## Scope

第三阶段合并为 3 个角色，均由同一开发者完成并自行提交 PR：

1. 页面闭环角色：让训练、评估、推荐、历史和导出流程可以直接在页面操作。
2. 推荐解释角色：增强推荐理由，让结果不只显示概率高低，还能给出可读的辅助解释。
3. 交付验收角色：补齐 CI、文档、演示流程、测试记录和 PR 检查材料。

本阶段不引入登录、权限、复杂后台管理、重型前端框架或数据库迁移工具。第三阶段优先使用现有 FastAPI、Jinja2、原生 JavaScript、SQLite、pytest 和 ECharts。

## Architecture

后端继续保持“路由薄、服务层承载业务逻辑”的结构。现有 API 路径和响应字段保持兼容；如需新增字段，只能做向后兼容扩展，不能删除 Phase 2 已有字段。GET 页面继续保持无副作用，不能在页面加载时自动训练模型、自动预测推荐或写入数据库。

前端继续沿用 Jinja2 模板和静态 CSS。交互逻辑使用页面内原生 JavaScript 调用现有 API，优先复用已有 `/api/models/train`、`/api/models/runs`、`/api/models/compare`、`/api/recommend/predict`、`/api/recommend/history`、`/api/recommend/export` 和 `/api/charts/*`。页面展示以表格、按钮、输入框和图表刷新为主，避免改成新的前端工程。

推荐解释优先复用现有 `reason` 字段，避免修改数据库结构。解释逻辑放在 `app/services/model_service.py` 的独立 helper 中，既能被 `predict_recommendations` 调用，也能被单元测试直接验证。

## Data Flow

训练流程：

1. 用户在 `/train` 选择模型。
2. 页面调用 `POST /api/models/train`。
3. 服务层训练模型、保存 `latest_model.joblib`、写入 SQLite 训练记录和指标记录。
4. 页面显示本次训练摘要，并刷新训练历史入口。

评估流程：

1. 用户打开 `/evaluate`。
2. 页面通过已有上下文展示最近一次模型指标。
3. ECharts 调用 `/api/charts/model-metrics` 展示模型对比。
4. 第三阶段补充最近训练记录列表，方便答辩时说明持久化效果。

推荐流程：

1. 用户在 `/recommend` 输入推荐数量。
2. 页面调用 `POST /api/recommend/predict`。
3. 服务层读取最新模型、计算概率、生成推荐等级和增强后的推荐理由。
4. 推荐结果写入 SQLite。
5. 页面展示结果表格、刷新等级分布图，并提供历史与 CSV 导出入口。

## Error Handling

- 页面操作失败时展示清晰的页面内错误信息，不只在控制台输出。
- API 的现有 400 和 422 行为保持不变。
- 前端对网络失败、空历史、无模型记录、空推荐结果分别展示不同提示。
- 推荐数量继续由后端校验为正整数，前端只做用户体验层面的辅助限制。

## Testing

第三阶段每个角色都需要保留全量回归命令：

```powershell
python -m pytest -q
```

页面闭环角色重点补充模板测试和 API 兼容测试。推荐解释角色重点补充 helper 单元测试和推荐 API 回归测试。交付验收角色重点补充 CI 文件检查、文档占位扫描和最终演示流程复核。

最终验收命令：

```powershell
python -m pytest -q
git diff --check
rg -n "TB[D]|TO[DO]|待补[充]" README.md docs
```

## PR Strategy

推荐拆成 3 个 PR：

1. `phase3/ui-workflow`：页面闭环。
2. `phase3/explain-recommendations`：推荐解释。
3. `phase3/ci-docs-demo`：CI、文档、演示和最终验收材料。

如果课程时间紧，也可以在当前 `phase3/productization` 分支上连续提交，再由同一个分支发一个总 PR。无论选择哪种方式，PR 描述都需要写明完成内容、修改文件、测试命令、测试结果和需要注意的兼容性。
