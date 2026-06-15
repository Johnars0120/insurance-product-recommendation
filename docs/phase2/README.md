# 第二阶段开发文档索引

本文档目录用于第二阶段小组分工、开发实施、PR 检查和答辩材料准备。第二阶段统一从 `phase2/integration` 开始，不直接修改 `main`。

## 当前开发基线

- GitHub 仓库：<https://github.com/Johnars0120/insurance-product-recommendation>
- 第二阶段集成分支：`phase2/integration`
- 已完成基础：第一阶段 MVP 已合并到 `main`；第二阶段 SQLite 基础表和数据库连接已完成。
- 第二阶段目标：持久化训练和推荐历史、多模型对比、图表展示、推荐结果导出、测试记录和答辩材料。

## 文档列表

| 文档 | 用途 |
| --- | --- |
| [第二阶段成员分工总览.md](第二阶段成员分工总览.md) | 组长分配任务、群通知、PR 合并顺序 |
| [组长集成验收开发文档.md](组长集成验收开发文档.md) | 分支管理、集成测试、最终验收 |
| [后端持久化开发文档.md](后端持久化开发文档.md) | 训练记录和模型指标 SQLite 持久化 |
| [数据算法开发文档.md](数据算法开发文档.md) | 决策树、随机森林、多模型指标对比 |
| [推荐结果开发文档.md](推荐结果开发文档.md) | 推荐历史、推荐结果持久化、CSV 导出 |
| [前端可视化开发文档.md](前端可视化开发文档.md) | ECharts 图表 API 和页面展示 |
| [文档测试答辩开发文档.md](文档测试答辩开发文档.md) | 测试记录、截图、接口说明、答辩流程 |
| [../第二阶段测试记录.md](../第二阶段测试记录.md) | 第二阶段自动化测试、页面/API 检查和截图清单 |
| [../答辩演示流程.md](../答辩演示流程.md) | 第二阶段现场演示脚本和讲解顺序 |

## 推荐分支

| 成员 | 角色 | 推荐分支 |
| --- | --- | --- |
| 组长 | 集成验收 | `phase2/integration` |
| 成员 A | 后端持久化 | `phase2/backend-history` |
| 成员 B | 数据与算法 | `phase2/model-compare` |
| 成员 C | 推荐结果模块 | `phase2/recommend-export` |
| 成员 D | 前端可视化 | `phase2/charts-ui` |
| 成员 E | 文档测试答辩 | `phase2/docs-qa` |

如果小组人数少于 6 人，可以合并角色：4 人组建议把“推荐结果模块”和“前端可视化”合并；5 人组建议由组长兼任最终文档验收。

## 开发前统一命令

```powershell
git fetch origin
git switch -c phase2/backend-history origin/phase2/integration
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
```

把 `phase2/backend-history` 替换成自己的分支名。

## PR 要求

每个 PR 必须写清楚：

```text
完成内容：
修改文件：
测试命令：
测试结果：
需要其他成员配合：
```

每个成员至少运行：

```powershell
python -m pytest -q
```

组长合并前需要确认 PR 只包含本成员负责范围内的修改。
