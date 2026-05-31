import os
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient

from app.main import app
import app.routers.pages as pages_router


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


def test_static_css_route_returns_stylesheet():
    client = TestClient(app)

    response = client.get("/static/css/main.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")


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
