# 第三阶段开发索引

本文档用于第三阶段开发分工、分支管理、PR 提交和最终验收。第三阶段统一从 `origin/main` 开始，不再从 `phase2/integration` 开始。

## 当前开发基线

- GitHub 仓库：<https://github.com/Johnars0120/insurance-product-recommendation>
- 第三阶段起点：`origin/main`
- 当前确认提交：`31d5324 feat: harden data workflow for final validation`
- 当前总开发分支：`main`
- 最终测试：`python -m pytest -q`，结果为 `78 passed`
- 健康检查：`GET /health` 返回 200

## 第三阶段完成内容

- 页面闭环：`/data`、`/train`、`/evaluate`、`/recommend` 已能支撑浏览器完整演示。
- 推荐解释：推荐结果包含购买概率、推荐等级和推荐理由。
- 数据隔离：上传数据写入 `data/runtime/`，不覆盖 `data/raw/` 样例数据。
- 模型版本化：训练模型保存为 `saved_models/{run_id}.joblib`，同时维护 `latest_model.joblib`。
- 交付验收：已补齐截图、测试记录、演示流程和算法实验说明。

## 开发前命令

```powershell
git fetch origin
git switch main
git pull origin main
python -m pytest -q
```

如果在本地仓库中继续开发：

```powershell
cd path\to\insurance-product-recommendation
git status --short --branch
python -m pytest -q
```

## PR 顺序

1. 先做页面闭环，让系统具备完整浏览器演示路径。
2. 再做推荐解释，让输出结果更有说服力。
3. 最后做 CI 与文档验收，把测试记录、演示步骤和截图清单补齐。

## 第三阶段交付材料

- CI 自动测试：[.github/workflows/tests.yml](../../.github/workflows/tests.yml)
- 测试记录：[docs/第三阶段测试记录.md](../第三阶段测试记录.md)
- 演示流程：[docs/第三阶段演示流程.md](../第三阶段演示流程.md)
- 答辩演示流程：[docs/答辩演示流程.md](../答辩演示流程.md)
- 算法实验补充说明：[docs/算法实验补充说明.md](../算法实验补充说明.md)
- 验收截图：`docs/screenshots/`

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
rg -n "TB[D]|TOD[O]|待补[充]" README.md docs
```

`rg` 命令没有输出时，表示文档占位扫描通过。
