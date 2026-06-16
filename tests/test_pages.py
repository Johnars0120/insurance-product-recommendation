import os
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest

from app.main import app
import app.routers.pages as pages_router


@pytest.fixture()
def client():
    return TestClient(app)


def test_first_stage_pages_render():
    client = TestClient(app)

    for path in ["/", "/data", "/train", "/evaluate", "/recommend"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "保险产品智能推荐系统" in response.text


def test_home_page_returns_html():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_page_nav_links_are_present():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    for href in ["/", "/data", "/train", "/evaluate", "/recommend", "/docs"]:
        assert f'href="{href}"' in response.text


def test_second_stage_pages_include_chart_containers():
    client = TestClient(app)

    expected_containers = {
        "/data?uploaded=1": 'id="dataset-chart"',
        "/evaluate": 'id="metrics-chart"',
        "/recommend": 'id="recommend-level-chart"',
    }

    for path, container in expected_containers.items():
        response = client.get(path)

        assert response.status_code == 200
        assert container in response.text


def test_data_page_contains_dataset_upload_controls(client):
    response = client.get("/data")

    assert response.status_code == 200
    expected_fragments = [
        'id="dataset-upload-form"',
        'class="upload-dropzone"',
        'data-file-input="train-file"',
        'data-file-input="eval-file"',
        'id="train-file"',
        'id="eval-file"',
        'accept=".xlsx,.csv"',
        'fetch("/api/datasets/upload"',
        "FormData(form)",
    ]
    for fragment in expected_fragments:
        assert fragment in response.text


def test_data_page_hides_dataset_analysis_before_upload(client):
    response = client.get("/data")

    assert response.status_code == 200
    assert "上传后显示数据分析" in response.text
    assert 'id="dataset-chart"' not in response.text
    assert "<dt>样本数</dt>" not in response.text


def test_data_page_shows_dataset_analysis_after_upload_flag(client):
    response = client.get("/data?uploaded=1")

    assert response.status_code == 200
    assert 'id="dataset-chart"' in response.text
    assert "<dt>样本数</dt>" in response.text


def test_frontend_pages_do_not_use_delivery_only_wording(client):
    forbidden_terms = ["答辩", "课程实践", "报告截图"]

    for path in ["/", "/data", "/train", "/evaluate", "/recommend"]:
        response = client.get(path)

        assert response.status_code == 200
        for term in forbidden_terms:
            assert term not in response.text


def test_recommend_page_links_to_export_api():
    client = TestClient(app)

    response = client.get("/recommend")

    assert response.status_code == 200
    assert 'id="recommend-level-chart"' in response.text
    assert 'href="/api/recommend/export"' in response.text


def test_train_page_contains_phase3_training_controls(client):
    response = client.get("/train")

    assert response.status_code == 200
    assert 'id="model-name"' in response.text
    assert 'id="train-model-button"' in response.text
    assert 'id="train-result"' in response.text


def test_train_page_contains_training_api_contract(client):
    response = client.get("/train")

    assert response.status_code == 200
    expected_fragments = [
        'fetch("/api/models/train"',
        'method: "POST"',
        "JSON.stringify({model_name: modelName})",
        "data.run_id",
        "data.model_name",
        "data.train_rows",
        "data.eval_rows",
        "data.metrics",
    ]
    for fragment in expected_fragments:
        assert fragment in response.text


def test_train_page_presents_productized_training_workflow(client):
    response = client.get("/train")

    assert response.status_code == 200
    expected_fragments = [
        "模型运营流程",
        "数据准备",
        "模型训练",
        "模型评估",
        "推荐生成",
        "训练控制台",
        "开始训练",
        "训练完成后可直接查看评估指标并生成推荐名单。",
        'class="status-box is-empty"',
        'href="/evaluate"',
    ]
    for fragment in expected_fragments:
        assert fragment in response.text


def test_evaluate_page_contains_recent_runs_table(client):
    response = client.get("/evaluate")

    assert response.status_code == 200
    assert 'id="recent-runs-table"' in response.text


def test_evaluate_page_contains_runs_api_contract(client):
    response = client.get("/evaluate")

    assert response.status_code == 200
    expected_fragments = [
        'fetch("/api/models/runs")',
        "if (!response.ok)",
        "<th>模型</th>",
        "<th>运行编号</th>",
        "<th>训练行数</th>",
        "<th>评估行数</th>",
        "<th>创建时间</th>",
    ]
    for fragment in expected_fragments:
        assert fragment in response.text


def test_evaluate_page_explains_metrics_and_next_action(client):
    response = client.get("/evaluate")

    assert response.status_code == 200
    expected_fragments = [
        "模型质量看板",
        "用于判断当前模型是否适合进入推荐环节。",
        "整体预测正确率",
        "推荐名单准确性",
        "潜在客户覆盖能力",
        "准确性与覆盖率平衡",
        "模型区分能力",
        'href="/recommend"',
        "生成推荐名单",
    ]
    for fragment in expected_fragments:
        assert fragment in response.text


def test_recommend_page_contains_phase3_prediction_controls(client):
    response = client.get("/recommend")

    assert response.status_code == 200
    assert 'id="recommend-limit"' in response.text
    assert 'id="predict-recommend-button"' in response.text
    assert 'id="recommend-results-table"' in response.text
    assert 'id="recommend-history-table"' in response.text


def test_recommend_page_contains_prediction_api_contract(client):
    response = client.get("/recommend")

    assert response.status_code == 200
    expected_fragments = [
        'fetch("/api/recommend/predict"',
        'method: "POST"',
        "JSON.stringify({limit: limit})",
        'fetch("/api/recommend/history")',
        "item.customer_id",
        "item.probability",
        "item.recommend_level",
        "item.reason",
        'step="1"',
        "Number(limitInput.value)",
        "Number.isInteger(limit)",
    ]
    for fragment in expected_fragments:
        assert fragment in response.text


def test_recommend_page_prioritizes_business_recommendation_flow(client):
    response = client.get("/recommend")

    assert response.status_code == 200
    expected_fragments = [
        "客户推荐工作台",
        "建议 20-100 条，适合人工跟进与导出。",
        "本次推荐结果",
        "购买概率",
        "高意向",
        "中意向",
        "低意向",
        'class="button button-secondary"',
        "导出 CSV",
        'id="recommend-limit-error"',
    ]
    for fragment in expected_fragments:
        assert fragment in response.text


def test_static_css_route_returns_stylesheet():
    client = TestClient(app)

    response = client.get("/static/css/main.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")


def test_static_css_keeps_secondary_button_hover_legible():
    client = TestClient(app)

    response = client.get("/static/css/main.css")

    assert response.status_code == 200
    css = response.text.replace("\r\n", "\n")
    assert ".button:not(.button-secondary):hover:not(:disabled)" in css
    assert ".button-secondary:hover" in css
    assert ".button-secondary:hover {\n    background: var(--surface-soft);\n    color: var(--accent-strong);" in css


def test_page_get_routes_do_not_train_or_predict(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("GET pages must not train or predict")

    monkeypatch.setattr(pages_router, "get_latest_run", lambda: None)
    monkeypatch.setattr(pages_router, "build_dataset_profile", lambda: {
        "target_column": "移动房车险数量",
        "target_positive_rate": 0.0,
        "feature_columns": ["age"],
        "train": {
            "file": "data.xlsx",
            "rows": 1,
            "columns": 2,
            "valid_target_count": 1,
            "positive_count": 0,
            "negative_count": 1,
            "positive_rate": 0.0,
            "missing_value_count": 0,
        },
        "eval": {
            "file": "eval.xlsx",
            "rows": 1,
            "columns": 2,
            "valid_target_count": 1,
            "positive_count": 0,
            "negative_count": 1,
            "positive_rate": 0.0,
            "missing_value_count": 0,
        },
    })
    monkeypatch.setattr("app.services.model_service.train_baseline_model", fail_if_called)
    monkeypatch.setattr("app.services.model_service.predict_recommendations", fail_if_called)

    client = TestClient(app)

    for path in ["/", "/data", "/train", "/evaluate", "/recommend"]:
        response = client.get(path)
        assert response.status_code == 200


def test_pages_and_static_work_when_imported_from_parent_cwd():
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(repo_root)
        if not existing_pythonpath
        else os.pathsep.join([str(repo_root), existing_pythonpath])
    )
    script = (
        "from fastapi.testclient import TestClient; "
        "from app.main import app; "
        "client = TestClient(app); "
        "assert client.get('/').status_code == 200; "
        "assert client.get('/static/css/main.css').status_code == 200"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo_root.parent,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
