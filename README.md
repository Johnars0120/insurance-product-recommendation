# 保险产品智能推荐系统

本仓库用于团队协作开发“保险产品智能推荐系统”。项目第一版采用轻量 Web 系统方案，重点跑通数据读取、模型训练、模型评估、保险推荐、页面展示和结果导出流程。

## 技术路线

- FastAPI：后端 Web 框架
- Jinja2：页面模板
- SQLite：本地轻量数据库
- Pandas / openpyxl：Excel 数据读取与处理
- scikit-learn：模型训练与评估
- ECharts：前端图表展示

## 快速运行

```powershell
git clone https://github.com/Johnars0120/insurance-product-recommendation.git
cd insurance-product-recommendation
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

浏览器访问：

```text
http://127.0.0.1:8000
```

接口文档地址：

```text
http://127.0.0.1:8000/docs
```

## 目录结构

```text
insurance-product-recommendation/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ database.py
│  ├─ routers/
│  ├─ services/
│  ├─ models/
│  ├─ templates/
│  └─ static/
├─ data/
│  ├─ raw/
│  ├─ processed/
│  └─ output/
├─ saved_models/
├─ docs/
├─ tests/
├─ requirements.txt
└─ README.md
```

## 分工建议

| 方向 | 分支 | 主要任务 |
| --- | --- | --- |
| 数据与算法 | `feature/data-model` | 数据读取、预处理、模型训练、模型评估、预测函数封装 |
| 后端接口 | `feature/backend` | FastAPI 路由、接口、SQLite 记录、服务层整合 |
| 前端展示 | `feature/frontend` | Jinja2 页面、静态样式、ECharts 图表、推荐结果展示 |
| 文档测试 | `feature/docs` | 开发记录、接口说明、测试记录、截图、答辩材料 |

## GitHub 协作规则

1. `main` 分支只放稳定版本。
2. 组员不要直接向 `main` 提交代码。
3. 每位组员在自己的功能分支上开发。
4. 每次开始开发前先同步最新代码。
5. 每完成一个小功能就提交一次 commit。
6. 功能完成后发 Pull Request，由组长检查后合并。
7. 涉及接口名称、字段名称、目录结构的修改，先在群里确认。


更多协作细节见 [docs/协同开发说明.md](docs/协同开发说明.md)。
