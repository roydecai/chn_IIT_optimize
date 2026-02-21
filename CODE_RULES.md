# 项目代码生成规则

## 1. 文件夹架构

```
项目根目录/
├── backend/          # 后端业务逻辑代码
│   ├── models/       # 数据模型和领域对象
│   └── services/     # 服务层（税务计算等业务逻辑）
├── data/             # 数据层
│   └── database.py   # 数据库操作
├── frontend/         # 前端代码（待开发）
├── scripts/          # 脚本工具
└── planning/         # 项目规划文档
```

## 2. 代码放置规则

| 代码类型 | 放置位置 |
|---------|---------|
| 业务逻辑/服务层 | `backend/services/` |
| 数据模型/领域对象 | `backend/models/` |
| 数据库操作 | `data/database.py` |
| 前端组件/页面 | `frontend/` |
| 工具脚本 | `scripts/` |

## 3. 导入路径规范

- 后端代码使用相对导入或绝对导入
- 示例：
  - `from backend.services.tax_calculator import xxx`
  - `from backend.models.entities import xxx`
  - `from data.database import xxx`

## 4. 命名规范

- Python文件：snake_case (如 `tax_calculator.py`)
- 类名：PascalCase (如 `Entity`)
- 函数名：snake_case (如 `calc_progressive_tax`)

## 5. 精度要求

- 所有货币计算必须使用 `decimal.Decimal`
- 舍入规则：银行家舍入 `ROUND_HALF_EVEN`
- 中间结果保留4位小数

## 6. 重要约束

- **禁止**在未取得用户准许的情况下创建新文件夹
- **禁止**修改现有文件夹架构
- 生成代码前先确认代码应放置的文件夹位置
