# 保险产品智能推荐系统

## 项目介绍

保险产品智能推荐系统是一个面向保险客户推荐场景的轻量级 Web 应用。系统基于历史客户数据训练分类模型，评估客户购买保险产品的可能性，并输出推荐等级、预测概率和推荐理由，帮助业务人员快速筛选值得优先跟进的客户。

项目采用 FastAPI + Jinja2 + SQLite + scikit-learn 的技术路线，重点覆盖数据上传、数据读取、模型训练、模型评估、推荐生成、历史记录、图表展示和 CSV 导出等完整流程。系统既可以通过浏览器页面操作，也可以通过 API 接口调用，适合作为保险推荐场景的原型系统和团队协作开发项目。

## 最终交付状态

当前版本对应课程最终交付口径，已完成从客户数据导入、数据预处理、模型训练、模型评估、客户推荐、推荐历史到 CSV 导出的业务闭环。项目使用课程提供的保险客户数据，训练集 5822 条、评估集 4000 条，每条记录 86 个字段，目标字段为 `移动房车险数量`。

最终验证结果：

- 自动化测试：`python -m pytest -q`，结果为 `78 passed`。
- 健康检查：`GET /health` 返回 `{"status":"ok","project":"insurance-product-recommendation"}`。
- 验收截图：已整理在 `docs/screenshots/`。
- 算法实验说明：见 [docs/算法实验补充说明.md](docs/算法实验补充说明.md)。

## 核心功能

- 数据概览：支持上传 `.xlsx` 或 `.csv` 格式的训练集和评估集，并在上传后展示字段数量、正负样本数量等信息。
- 模型训练：支持 `logistic_regression`、`decision_tree`、`random_forest` 三类模型训练。
- 模型评估：展示 Accuracy、Precision、Recall、F1、AUC 等指标，并保存每次训练记录。
- 模型对比：按模型类型查看最近训练结果，方便比较不同算法表现。
- 智能推荐：根据最新模型对客户生成推荐结果，输出预测概率、推荐等级和推荐理由。
- 推荐历史：保存推荐批次和推荐明细，系统重启后仍可查询。
- 结果导出：支持将推荐结果导出为 CSV 文件。
- 图表展示：使用 ECharts 展示样本分布、模型指标和推荐等级分布。
- 自动测试：提供页面、接口、数据库、模型服务和推荐历史等测试用例。

## 技术路线

| 模块 | 技术 |
| --- | --- |
| 后端框架 | FastAPI |
| 页面模板 | Jinja2 |
| 数据库 | SQLite、SQLAlchemy |
| 数据处理 | Pandas、openpyxl、NumPy |
| 机器学习 | scikit-learn、joblib |
| 图表展示 | ECharts |
| 自动测试 | pytest、httpx |

## 环境要求

建议使用以下环境运行项目：

- Windows 10/11
- Python 3.10 或更高版本
- Git
- 浏览器：Edge、Chrome 或 Firefox

可以通过下面命令确认 Python 和 Git 是否可用：

```powershell
python --version
git --version
```

## 快速启动

### 方式一：一键启动

Windows 用户可以直接双击项目根目录下的：

```text
run_app.bat
```

脚本会自动进入项目目录、创建 `.venv` 虚拟环境、安装依赖、打开浏览器并启动服务。

启动成功后访问：

```text
http://127.0.0.1:8000
```

停止服务时，在脚本窗口按 `Ctrl+C`，然后按提示退出即可。

如果想指定端口或跳过依赖安装，可以使用 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_app.ps1 -Port 8001
powershell -ExecutionPolicy Bypass -File scripts\run_app.ps1 -SkipInstall -NoBrowser
powershell -ExecutionPolicy Bypass -File scripts\run_app.ps1 -Reload
```

### 方式二：手动启动

#### 1. 获取项目代码

```powershell
git clone https://github.com/Johnars0120/insurance-product-recommendation.git
cd insurance-product-recommendation
```

如果已经有本地仓库，直接进入项目目录并同步最新代码：

```powershell
cd path\to\insurance-product-recommendation
git switch main
git pull origin main
```

#### 2. 创建并激活虚拟环境

```powershell
python -m venv .venv
.venv\Scripts\activate
```

激活成功后，命令行前面通常会出现 `(.venv)`。

#### 3. 安装依赖

```powershell
pip install -r requirements.txt
```

如果下载速度较慢，可以使用国内镜像：

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 4. 启动系统

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动后浏览器访问：

```text
http://127.0.0.1:8000
```

接口文档地址：

```text
http://127.0.0.1:8000/docs
```

健康检查地址：

```text
http://127.0.0.1:8000/health
```

## 页面使用教程

推荐按照下面顺序使用系统。

### 1. 首页

访问：

```text
http://127.0.0.1:8000/
```

首页用于进入数据概览、模型训练、模型评估和保险推荐等主要页面。

### 2. 数据概览

访问：

```text
http://127.0.0.1:8000/data
```

数据概览页面会读取本地 Excel 数据文件，展示训练集和评估集的基本情况。页面中的图表用于查看训练数据中正样本和负样本的数量分布。

页面也提供数据上传入口，可以上传新的训练集和评估集。上传文件要求：

- 文件格式为 `.xlsx` 或 `.csv`
- 两个文件都包含目标字段 `移动房车险数量`
- 训练集和评估集的特征字段保持一致

上传成功后，系统会把新数据写入运行时目录并清理已生成的模型文件。仓库自带的样例数据不会被覆盖；请重新训练模型后再查看评估和推荐结果。

项目自带样例数据文件位置：

```text
data/raw/data.xlsx
data/raw/eval.xlsx
```

上传后的运行时数据文件位置：

```text
data/runtime/data.xlsx
data/runtime/eval.xlsx
```

如果需要手动替换运行时数据文件，建议保持文件名不变，并确保训练集和评估集都包含目标字段：

```text
移动房车险数量
```

### 3. 模型训练

访问：

```text
http://127.0.0.1:8000/train
```

训练页面支持选择模型并发起训练。当前支持的模型名称包括：

| 模型名称 | 说明 |
| --- | --- |
| `logistic_regression` | 逻辑回归，适合作为基线模型 |
| `decision_tree` | 决策树，便于解释规则和特征划分 |
| `random_forest` | 随机森林，适合提升整体预测稳定性 |

训练完成后，系统会按训练批次保存模型文件和训练记录，同时维护一个最新模型别名：

```text
saved_models/{run_id}.joblib
saved_models/latest_model.joblib
```

训练记录会写入本地 SQLite 数据库。数据库文件属于本地运行产物，不需要提交到仓库。

### 4. 模型评估

访问：

```text
http://127.0.0.1:8000/evaluate
```

模型评估页面用于查看最近训练模型的指标结果，包括：

- Accuracy：整体预测准确率
- Precision：预测为正样本时的准确程度
- Recall：正样本被识别出来的比例
- F1：Precision 和 Recall 的综合指标
- AUC：模型区分正负样本的能力

页面也会展示不同模型的指标对比图，方便选择更适合当前数据的模型。

### 5. 智能推荐

访问：

```text
http://127.0.0.1:8000/recommend
```

推荐页面会基于最新训练模型生成客户推荐结果。推荐结果包含：

- 客户编号
- 预测购买概率
- 推荐等级：`high`、`medium`、`low`
- 推荐理由

推荐等级规则：

| 推荐等级 | 概率范围 | 建议 |
| --- | --- | --- |
| `high` | 大于等于 70% | 优先跟进 |
| `medium` | 40% 到 70% | 可结合人工判断继续触达 |
| `low` | 小于 40% | 暂缓高优先级推荐 |

生成推荐后，可以在页面查看历史推荐结果，也可以导出 CSV 文件用于提交、汇报或进一步分析。

## API 使用说明

系统启动后，可以通过 `http://127.0.0.1:8000/docs` 查看自动生成的接口文档。下面列出常用接口。

### 数据概览

```http
GET /api/datasets/profile
```

返回训练集和评估集的数据行数、字段数量、正负样本统计等信息。

### 上传数据集

```http
POST /api/datasets/upload
Content-Type: multipart/form-data
```

表单字段：

```text
train_file: 训练集 .xlsx 文件
eval_file: 评估集 .xlsx 文件
```

上传成功后，系统会写入 `data/runtime/` 下的训练集和评估集，并清理所有已生成模型文件。请重新训练模型后再生成推荐结果。

如果设置了环境变量 `INSURANCE_RECOMMENDATION_ADMIN_TOKEN`，上传接口需要携带同值请求头：

```http
X-Admin-Token: your-token
```

### 训练模型

```http
POST /api/models/train
Content-Type: application/json

{
  "model_name": "logistic_regression"
}
```

`model_name` 可选值：

```text
logistic_regression
decision_tree
random_forest
```

### 查看训练记录

```http
GET /api/models/runs
```

返回历史模型训练记录。

### 对比模型指标

```http
GET /api/models/compare
```

返回不同模型最近一次训练的指标对比。

### 查看最近模型评估结果

```http
GET /api/models/evaluate
```

如果还没有训练记录，该接口会返回 `404`。先训练模型后再查看评估结果即可。

### 生成推荐结果

```http
POST /api/recommend/predict
Content-Type: application/json

{
  "limit": 20
}
```

`limit` 表示本次最多生成多少条推荐结果。

### 查看推荐历史

```http
GET /api/recommend/history
```

也可以指定推荐批次和数量：

```http
GET /api/recommend/history?run_id=推荐批次ID&limit=100
```

### 导出推荐结果

```http
GET /api/recommend/export
```

返回 CSV 文件，字段包括：

```text
customer_id, probability, recommend_level, reason
```

### 图表数据接口

```http
GET /api/charts/dataset
GET /api/charts/model-metrics
GET /api/charts/recommend-levels
```

这些接口主要供前端 ECharts 图表使用。

## 测试方法

运行全部测试：

```powershell
python -m pytest -q
```

项目测试覆盖内容包括：

- 应用启动和健康检查
- 页面访问
- 数据集概览
- 模型训练与评估
- 模型历史记录
- 模型对比接口
- 推荐生成接口
- 推荐历史和导出
- 图表数据接口
- SQLite 持久化逻辑

如果测试过程中生成了本地数据库、模型文件或缓存文件，这些属于运行产物，已经通过 `.gitignore` 排除。

最终验收时建议同时检查服务健康状态：

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端访问：

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
```

## 常见问题

### 端口 8000 被占用

可以换一个端口启动：

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

然后访问：

```text
http://127.0.0.1:8001
```

### 依赖安装失败

先确认虚拟环境已激活，再升级 pip：

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

如果网络较慢，可以使用镜像源安装。

### 页面没有推荐结果

推荐结果依赖模型文件。如果还没有训练过模型，可以先进入训练页面训练一个模型，再进入推荐页面生成推荐。接口层面也会在缺少模型时自动训练默认模型，但建议先手动训练，流程更清晰。

### 模型评估接口返回 404

说明当前还没有模型训练记录。先访问 `/train` 页面训练模型，或调用 `/api/models/train` 接口。

### 替换数据后训练失败

请检查训练集和评估集是否都包含目标字段 `移动房车险数量`，并确保训练集和评估集的特征字段一致。

## 目录结构

```text
insurance-product-recommendation/
├─ .github/
│  ├─ workflows/
│  └─ pull_request_template.md
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
│  │  ├─ data.xlsx
│  │  └─ eval.xlsx
│  ├─ runtime/
│  ├─ processed/
│  └─ output/
├─ docs/
├─ saved_models/
├─ tests/
├─ CONTRIBUTORS.md
├─ requirements.txt
└─ README.md
```

主要目录说明：

| 路径 | 说明 |
| --- | --- |
| `app/main.py` | FastAPI 应用入口 |
| `app/routers/` | 页面和 API 路由 |
| `app/services/` | 数据处理、模型训练、历史记录等业务逻辑 |
| `app/models/` | 数据库模型定义 |
| `app/templates/` | Jinja2 页面模板 |
| `app/static/` | CSS 等静态资源 |
| `data/raw/` | 仓库自带样例 Excel 数据 |
| `data/runtime/` | 上传后的本地运行时数据，已通过 `.gitignore` 排除 |
| `docs/` | 项目文档、测试记录和使用流程 |
| `saved_models/` | 本地训练模型输出目录，模型文件已通过 `.gitignore` 排除 |
| `tests/` | 自动化测试用例 |

## 项目文档

- [接口说明](docs/接口说明.md)
- [算法实验补充说明](docs/算法实验补充说明.md)
- [开发任务看板](docs/开发任务看板.md)
- [协同开发说明](docs/协同开发说明.md)
- [第二阶段测试记录](docs/第二阶段测试记录.md)
- [第三阶段测试记录](docs/第三阶段测试记录.md)
- [第三阶段演示流程](docs/第三阶段演示流程.md)

## 协作规则

1. `main` 分支只保留稳定版本。
2. 开发新功能前先同步最新代码。
3. 新功能建议从 `origin/main` 新建独立分支。
4. 每完成一个相对独立的小功能就提交一次 commit。
5. 功能完成后发起 Pull Request，再合并到 `main`。
6. 涉及接口名称、字段名称、目录结构的调整，先在团队内确认。

新建开发分支示例：

```powershell
git fetch origin
git switch -c feature/your-feature origin/main
```

## 当前状态

项目当前已完成数据上传、基础推荐闭环、持久化记录、多模型对比、图表展示、推荐历史、CSV 导出、截图材料和自动化测试。仓库中的代码与文档可作为课程最终演示版本使用；Word 版计划书和说明书作为课程提交材料单独管理，不放入代码仓库。
