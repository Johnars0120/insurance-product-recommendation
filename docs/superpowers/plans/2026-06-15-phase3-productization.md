# Phase 3 Productization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a third-stage productized version where the browser can drive the full model-training and recommendation workflow, recommendation reasons are more useful, and delivery is covered by CI plus demonstration documents.

**Architecture:** Keep FastAPI routers thin and preserve all Phase 2 API paths. Put recommendation explanation logic in `app/services/model_service.py`, keep persistence in `history_service.py`, and add page interactions through the existing Jinja2 templates plus small page-local JavaScript. GET pages must stay read-only and must not train models, run predictions, or write database rows.

**Tech Stack:** FastAPI, Jinja2, SQLite, SQLAlchemy, pandas, scikit-learn, joblib, ECharts, pytest, TestClient, GitHub Actions.

---

## Current Context

- Work starts from `origin/main` at `78406b1 docs: confirm recommendation contributor credit`.
- The Phase 3 worktree is `.worktrees/phase3-productization`.
- The current total branch is `phase3/productization`.
- Baseline verification in the Phase 3 worktree: `python -m pytest -q` => `53 passed`.
- The project already has model training, model comparison, recommendation prediction, recommendation history, CSV export, chart APIs, and documentation from Phase 2.

## File Structure

- `app/templates/train.html`: add model selector, training button, status area, and latest training result panel.
- `app/templates/evaluate.html`: add recent training runs table while keeping the existing metrics panel and ECharts chart.
- `app/templates/recommend.html`: add recommendation form, results table, history refresh, export link, and page-level error handling.
- `app/static/css/main.css`: add small reusable styles for forms, buttons, tables, status messages, and responsive result areas.
- `app/services/model_service.py`: add tested helper functions for richer recommendation reasons while preserving existing API response fields.
- `tests/test_pages.py`: assert the new controls and tables exist and GET pages remain side-effect free.
- `tests/test_recommendation_api.py`: add coverage for enhanced recommendation reasons and preserve export compatibility.
- `.github/workflows/tests.yml`: run pytest on pull requests and pushes.
- `README.md`: update Phase 3 status and remove Phase 2-only branch guidance from the main workflow.
- `docs/phase3/README.md`: keep role, branch, and PR workflow guidance.
- `docs/第三阶段测试记录.md`: record commands, results, page checklist, API checklist, and screenshot checklist.
- `docs/第三阶段演示流程.md`: provide browser-first demo steps for the final presentation.

## Global Rules

- Preserve existing API paths and existing response field names.
- Do not delete `reason`; improve its contents.
- Do not add a new frontend framework.
- Do not make GET page requests trigger model training, predictions, database writes, or CSV exports.
- Keep generated files out of Git: SQLite databases, saved model files, exported CSV files, screenshots not intentionally added to `docs/screenshots`.
- Each implementation task should end with `python -m pytest -q`.

---

### Task 1: Page Workflow Controls

**Goal:** Let users train models and generate recommendations directly from the browser pages.

**Files:**
- Modify: `app/templates/train.html`
- Modify: `app/templates/evaluate.html`
- Modify: `app/templates/recommend.html`
- Modify: `app/static/css/main.css`
- Test: `tests/test_pages.py`

- [ ] **Step 1: Write failing page tests**

Add tests that assert the new controls exist without triggering side effects:

```python
def test_train_page_contains_phase3_training_controls(client):
    response = client.get("/train")

    assert response.status_code == 200
    assert 'id="model-name"' in response.text
    assert 'id="train-model-button"' in response.text
    assert 'id="train-result"' in response.text


def test_evaluate_page_contains_recent_runs_table(client):
    response = client.get("/evaluate")

    assert response.status_code == 200
    assert 'id="recent-runs-table"' in response.text


def test_recommend_page_contains_phase3_prediction_controls(client):
    response = client.get("/recommend")

    assert response.status_code == 200
    assert 'id="recommend-limit"' in response.text
    assert 'id="predict-recommend-button"' in response.text
    assert 'id="recommend-results-table"' in response.text
    assert 'id="recommend-history-table"' in response.text
```

- [ ] **Step 2: Run the page tests and confirm they fail**

```powershell
python -m pytest tests/test_pages.py -q
```

Expected result: fail because the new element ids are not present yet.

- [ ] **Step 3: Add training controls to `app/templates/train.html`**

Add a model selector with these exact values:

```html
<select id="model-name" name="model_name">
    <option value="logistic_regression">逻辑回归</option>
    <option value="decision_tree">决策树</option>
    <option value="random_forest">随机森林</option>
</select>
<button id="train-model-button" class="button" type="button">训练模型</button>
<div id="train-result" class="status-box" aria-live="polite"></div>
```

Add JavaScript that calls:

```javascript
fetch("/api/models/train", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({model_name: modelName})
})
```

Render `run_id`, `model_name`, `train_rows`, `eval_rows`, and metrics into `#train-result`.

- [ ] **Step 4: Add recent run display to `app/templates/evaluate.html`**

Add a table with id `recent-runs-table`. Populate it from the page context if available, or fetch `/api/models/runs` on page load. Columns should be:

```text
模型
运行编号
训练行数
评估行数
创建时间
```

- [ ] **Step 5: Add recommendation controls to `app/templates/recommend.html`**

Add:

```html
<input id="recommend-limit" name="limit" type="number" min="1" value="20">
<button id="predict-recommend-button" class="button" type="button">生成推荐</button>
<div id="recommend-status" class="status-box" aria-live="polite"></div>
<table id="recommend-results-table" class="data-table"></table>
<table id="recommend-history-table" class="data-table"></table>
```

The button should call `POST /api/recommend/predict` and render `customer_id`, `probability`, `recommend_level`, and `reason`.

- [ ] **Step 6: Add minimal CSS support**

Add reusable styles:

```css
.form-row {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: flex-end;
}

.button {
    min-height: 38px;
    border: 0;
    border-radius: 6px;
    padding: 0 14px;
    background: var(--accent);
    color: #ffffff;
    font-weight: 700;
    cursor: pointer;
}

.button:disabled {
    opacity: 0.58;
    cursor: wait;
}

.status-box {
    margin-top: 12px;
    color: var(--muted);
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
}

.data-table th,
.data-table td {
    border-bottom: 1px solid var(--line);
    padding: 10px 8px;
    text-align: left;
    vertical-align: top;
}
```

- [ ] **Step 7: Run targeted and full tests**

```powershell
python -m pytest tests/test_pages.py -q
python -m pytest -q
```

Expected result: all tests pass.

- [ ] **Step 8: Commit the page workflow**

```powershell
git add app/templates/train.html app/templates/evaluate.html app/templates/recommend.html app/static/css/main.css tests/test_pages.py
git commit -m "feat: add phase3 browser workflow controls"
```

---

### Task 2: Recommendation Explanation

**Goal:** Improve recommendation reasons while keeping the existing `reason` response field and CSV export compatible.

**Files:**
- Modify: `app/services/model_service.py`
- Modify: `tests/test_recommendation_api.py`

- [ ] **Step 1: Write failing helper tests**

Add tests for a new helper named `_build_recommendation_reason`:

```python
def test_build_recommendation_reason_mentions_high_probability():
    reason = model_service._build_recommendation_reason(
        probability=0.82,
        level="high",
        row={"age": 45, "income": 9000, "claims": 0},
    )

    assert "购买概率较高" in reason
    assert "82.00%" in reason


def test_build_recommendation_reason_mentions_medium_probability():
    reason = model_service._build_recommendation_reason(
        probability=0.55,
        level="medium",
        row={"age": 35, "income": 5200, "claims": 1},
    )

    assert "购买概率中等" in reason
    assert "55.00%" in reason


def test_build_recommendation_reason_mentions_low_probability():
    reason = model_service._build_recommendation_reason(
        probability=0.18,
        level="low",
        row={"age": 25, "income": 3000, "claims": 2},
    )

    assert "购买概率较低" in reason
    assert "18.00%" in reason
```

- [ ] **Step 2: Run the helper tests and confirm they fail**

```powershell
python -m pytest tests/test_recommendation_api.py -q
```

Expected result: fail because `_build_recommendation_reason` does not exist.

- [ ] **Step 3: Add `_build_recommendation_reason`**

Add this helper in `app/services/model_service.py` near `_recommend_level`:

```python
def _format_feature_hint(row):
    hints = []
    for column in ("age", "income", "claims"):
        if column in row:
            hints.append(f"{column}={row[column]}")
    if not hints:
        return "当前客户特征已纳入模型综合判断"
    return "关键特征：" + "，".join(hints)


def _build_recommendation_reason(probability, level, row):
    probability_text = f"{probability:.2%}"
    level_messages = {
        "high": "购买概率较高，建议优先跟进",
        "medium": "购买概率中等，可结合人工复核安排触达",
        "low": "购买概率较低，建议暂缓高优先级推荐",
    }
    message = level_messages.get(level, "模型已生成推荐判断")
    return f"{message}；预测概率为 {probability_text}；{_format_feature_hint(row)}"
```

- [ ] **Step 4: Use the helper during prediction**

Inside `predict_recommendations`, convert each evaluation row to a dict and call the helper:

```python
row = eval_data.iloc[row_index - 1].to_dict()
reason = _build_recommendation_reason(
    probability=probability,
    level=level,
    row=row,
)
```

Then set:

```python
"reason": reason,
```

- [ ] **Step 5: Add API compatibility assertion**

Extend the existing prediction API test:

```python
assert "预测概率" in first["reason"]
assert first["reason"]
```

- [ ] **Step 6: Run targeted and full tests**

```powershell
python -m pytest tests/test_recommendation_api.py -q
python -m pytest -q
```

Expected result: all tests pass.

- [ ] **Step 7: Commit the explanation change**

```powershell
git add app/services/model_service.py tests/test_recommendation_api.py
git commit -m "feat: improve recommendation explanations"
```

---

### Task 3: CI and Delivery Documents

**Goal:** Add automated test execution and Phase 3 delivery materials.

**Files:**
- Create: `.github/workflows/tests.yml`
- Modify: `README.md`
- Create: `docs/第三阶段测试记录.md`
- Create: `docs/第三阶段演示流程.md`
- Modify: `docs/phase3/README.md`

- [ ] **Step 1: Add GitHub Actions workflow**

Create `.github/workflows/tests.yml`:

```yaml
name: tests

on:
  push:
    branches:
      - main
      - "phase3/**"
  pull_request:

jobs:
  pytest:
    runs-on: windows-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: python -m pip install -r requirements.txt

      - name: Run tests
        run: python -m pytest -q
```

- [ ] **Step 2: Update README Phase 3 guidance**

In `README.md`, add a short section after “第二阶段新增能力”:

```markdown
## 第三阶段开发方向

第三阶段从 `origin/main` 开始，重点补充页面操作闭环、推荐理由增强、CI 自动测试和演示验收材料。第二阶段的 `codex/phase2-development` 已不再作为新功能开发基线。
```

Also adjust any active instruction that says second-stage development should still start from `codex/phase2-development`; keep it only as historical context if needed.

- [ ] **Step 3: Create Phase 3 test record**

Create `docs/第三阶段测试记录.md` with these sections:

```markdown
# 第三阶段测试记录

## 测试环境

| 项目 | 内容 |
| --- | --- |
| 日期 | 2026-06-15 |
| 分支 | `phase3/productization` |
| Python | `Python 3.11.9` |
| 测试框架 | `pytest` |

## 自动化测试

| 日期 | 命令 | 结果 | 备注 |
| --- | --- | --- | --- |
| 2026-06-15 | `python -m pytest -q` | 通过，53 passed | Phase 3 基线验证 |

## 页面检查清单

| 页面 | 检查内容 | 状态 |
| --- | --- | --- |
| `/train` | 可选择模型并触发训练 | 未执行 |
| `/evaluate` | 可查看最近指标、模型对比和训练记录 | 未执行 |
| `/recommend` | 可输入数量、生成推荐、查看历史和导出 CSV | 未执行 |

## 最终验收命令

```powershell
python -m pytest -q
git diff --check
rg -n "TB[D]|TO[DO]|待补[充]" README.md docs
```
```

- [ ] **Step 4: Create Phase 3 demo flow**

Create `docs/第三阶段演示流程.md` with a browser-first script:

```markdown
# 第三阶段演示流程

## 启动服务

```powershell
python -m pytest -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 演示顺序

1. 打开 `/`，说明系统目标和第三阶段新增页面闭环。
2. 打开 `/train`，选择三种模型之一并点击训练。
3. 打开 `/evaluate`，展示最近指标、模型对比图和训练记录。
4. 打开 `/recommend`，输入推荐数量并生成推荐结果。
5. 展示推荐等级、预测概率和增强后的推荐理由。
6. 打开推荐历史并导出 CSV。
7. 打开 GitHub Actions 页面，展示 PR 自动测试结果。
```

- [ ] **Step 5: Run delivery checks**

```powershell
python -m pytest -q
git diff --check
rg -n "TB[D]|TO[DO]|待补[充]" README.md docs
```

Expected result: pytest passes, `git diff --check` exits 0, and the `rg` command has no output.

- [ ] **Step 6: Commit delivery materials**

```powershell
git add .github/workflows/tests.yml README.md docs
git commit -m "docs: add phase3 delivery workflow"
```

---

## Final PR Checklist

- [ ] Branch starts from `origin/main`, not `codex/phase2-development`.
- [ ] `python -m pytest -q` passes.
- [ ] `git diff --check` passes.
- [ ] `rg -n "TB[D]|TO[DO]|待补[充]" README.md docs` has no output.
- [ ] Runtime files are not staged: `*.db`, `*.sqlite`, `saved_models/*.joblib`, exported CSV files.
- [ ] PR description includes completed content, modified files, test command, test result, compatibility notes, and screenshots or demo notes.
