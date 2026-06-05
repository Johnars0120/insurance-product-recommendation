# phase2/recommend-export 变更说明

> 负责人：马力 | 分支：`phase2/recommend-export`  
> 模块：推荐结果入库、历史查询、CSV 导出  
> 最后更新：2026-06-05

---

## 一、变更概览

| 操作 | 文件 | 说明 |
| --- | --- | --- |
| 修改 | `app/database.py` | 新增 SQLAlchemy engine、Session、Base 声明基类、`init_db()` |
| 修改 | `app/main.py` | 注册推荐路由、启动时自动建表 |
| 新增 | `app/models/recommendation.py` | 推荐结果数据库表模型 |
| 新增 | `app/services/recommend_service.py` | 入库、查询、导出核心逻辑 |
| 新增 | `app/routers/recommend.py` | 推荐相关 API 路由（4个接口） |

---

## 二、已完成的 API 接口

访问 `http://127.0.0.1:8000/docs` 可直接查看和测试所有接口。

### 2.1 `POST /api/recommend/predict` — 保存推荐结果

**请求体：**
```json
{
  "predictions": [
    {
      "customer_id": "C001",
      "probability": 0.82,
      "recommend_level": "high",
      "reason": "模型预测购买概率较高"
    },
    {
      "customer_id": "C002",
      "probability": 0.35,
      "recommend_level": "low",
      "reason": "模型预测购买概率较低"
    }
  ]
}
```

**说明：**
- `recommend_level` 和 `reason` 可以不传，系统自动生成
- 自动生成规则：≥0.70→high、0.40~0.70→medium、<0.40→low
- 返回 `batch_id`，同一批次数据共享一个 batch_id，方便后续查询和导出

**返回示例：**
```json
{
  "batch_id": "a1b2c3d4e5f6",
  "saved_count": 1000,
  "level_counts": {
    "high": 120,
    "medium": 300,
    "low": 580
  }
}
```

---

### 2.2 `GET /api/recommend/history` — 历史查询（分页）

**参数：**

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `batch_id` | string | 否 | 按批次筛选 |
| `recommend_level` | string | 否 | 按等级筛选：high/medium/low |
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页条数，默认 50，最大 500 |

**示例：**
```
GET /api/recommend/history?batch_id=a1b2c3d4e5f6&recommend_level=high&page=1&page_size=20
```

---

### 2.3 `GET /api/recommend/batches` — 批次列表

返回所有批次的 ID、记录数和最新时间，供前端做下拉选择。

**返回示例：**
```json
[
  {
    "batch_id": "a1b2c3d4e5f6",
    "record_count": 1000,
    "latest_time": "2026-06-05T15:30:00"
  }
]
```

---

### 2.4 `GET /api/recommend/export` — CSV 导出下载

**参数：**

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `batch_id` | string | 否 | 导出指定批次，不传则导出全部 |
| `recommend_level` | string | 否 | 按等级筛选导出 |

**示例：**
```
GET /api/recommend/export?batch_id=a1b2c3d4e5f6
```
浏览器会直接下载 CSV 文件，包含字段：customer_id、probability、recommend_level、reason、batch_id、created_at。

---

## 三、数据库表结构

表名：`recommendations`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INTEGER | 主键，自增 |
| `customer_id` | VARCHAR(64) | 客户编号（有索引） |
| `probability` | FLOAT | 预测购买概率 |
| `recommend_level` | VARCHAR(16) | high / medium / low |
| `reason` | VARCHAR(256) | 推荐理由 |
| `batch_id` | VARCHAR(64) | 批次标识（有索引） |
| `created_at` | DATETIME | 入库时间，自动生成 |

---

## 四、其他同学需要配合的工作

### 🔵 数据与算法同学（成员 B，`phase2/model-compare`）

**你需要做的：**

1. 训练完模型后，对 `data/raw/eval.xlsx`（评估数据）跑预测，得到每个客户的购买概率
2. 将预测结果整理成以下 JSON 格式，调用马力的 API 入库：

```python
import requests

predictions = []
for idx, row in df.iterrows():
    predictions.append({
        "customer_id": str(row.get("客户编号", idx)),
        "probability": float(your_model.predict_proba(...)),
        # recommend_level 和 reason 可以不传，系统自动生成
    })

requests.post("http://127.0.0.1:8000/api/recommend/predict", json={
    "predictions": predictions
})
```

3. 或者：你封装一个函数 `predict_all(eval_data_path) -> list[dict]`，马力来调也行

---

### 🟢 后端同学（成员 A，`phase2/backend-history`）

**你需要做的：**

1. C的 `database.py` 已经加了 `engine`、`SessionLocal`、`Base`、`init_db()`
   - 你的数据库表模型也继承 `from app.database import Base`
   - 你的数据库操作也使用 `from app.database import SessionLocal`
2. 如果你有自己的表模型，确保放在 `app/models/` 下，并且 `Base.metadata.create_all()` 会自动建表（已在 `main.py` 启动时调用 `init_db()`）

---

### 🟡 前端同学（成员 D，`phase2/charts-ui`）

**你可以使用C提供的 API 来展示推荐结果：**

| 需求 | 调哪个接口 |
| --- | --- |
| 推荐结果列表（带分页） | `GET /api/recommend/history?page=1&page_size=20` |
| 按推荐等级筛选 | `GET /api/recommend/history?recommend_level=high` |
| 批次下拉选择 | `GET /api/recommend/batches` |
| 导出按钮 | `GET /api/recommend/export?batch_id=xxx`（直接下载） |
| 等级分布统计 | 调用 history 后自己前端统计，或看 predict 返回的 `level_counts` |

---

### 🟣 文档测试同学（成员 E，`phase2/docs-qa`）

**测试清单：**
- [ ] `POST /api/recommend/predict` 批量入库是否正常，返回 `batch_id` 和各级别数量
- [ ] `GET /api/recommend/history` 分页查询是否正常，筛选功能是否生效
- [ ] `GET /api/recommend/batches` 是否返回正确的批次列表
- [ ] `GET /api/recommend/export` 是否能正常下载 CSV，中文不乱码
- [ ] API 文档页 `/docs` 是否能看到所有接口且格式正确
- [ ] 截图保存到 `docs/screenshots/`

---

## 五、已完成的工作总结

- [x] SQLite 推荐结果表设计与建表
- [x] 推荐结果批量入库（自动生成等级、推荐理由、批次号）
- [x] 推荐历史分页查询（支持按批次、等级筛选）
- [x] 批次列表查询
- [x] CSV 导出下载（UTF-8 BOM 编码，Excel 直接打开不乱码）
- [x] 基础测试通过
