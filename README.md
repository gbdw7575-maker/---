# 智能化健康管理系统

AI 驱动的个人健康管理平台 — OCR 体检报告识别 + 健康数据分析 + AI 健康咨询

---

## 快速开始

```bash
# 1. 确保 MySQL 已启动
# 2. 启动后端
cd backend
pip install -r requirements.txt
# 仓库未包含模型时可执行（正常 clone 已自带 10.35 MB ONNX 权重）
python -m app.classifier.download_model
uvicorn main:app --reload --port 8000
```

**或双击 `start.bat` 一键启动。**

---

## 访问地址

| 地址 | 说明 |
|------|------|
| http://localhost:8000/docs | Swagger API 文档 |
| http://localhost:8000/redoc | ReDoc API 文档 |
| http://localhost:8000/api/health | 健康检查 |

---

## 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | >= 3.11 | 后端运行环境 |
| MySQL | 8.0 | 数据库（已安装于 `E:\d\MySQL`） |
| Node.js（开发前端时） | >= 18 | 前端构建 |

---

## 项目结构

```
D:\code\health\
├── start.bat                    # 一键启动脚本
├── README.md                    # 本文件
├── 项目开发状态.md              # 详细开发状态
├── 产品介绍_智能化健康管理系统.md # 产品文档
└── backend/
    ├── main.py                  # FastAPI 入口
    ├── config.py                # 配置（环境变量）
    ├── requirements.txt         # Python 依赖
    ├── .env                     # 环境变量（数据库/API Key）
    └── app/
        ├── database.py          # 数据库连接配置
        ├── models/              # SQLAlchemy 数据模型
        │   ├── user.py
        │   ├── health_indicator.py
        │   └── chat.py
        ├── schemas/             # Pydantic 请求/响应模型
        │   ├── user.py
        │   ├── health_indicator.py
        │   ├── chat.py
        │   └── ocr.py
        ├── routers/             # API 路由
        │   ├── user.py
        │   ├── health.py
        │   ├── chat.py
        │   └── ocr.py
        └── services/            # 业务逻辑层
            ├── rule_engine.py   # 医学规则引擎（6类20项指标）
            ├── ai_service.py    # DeepSeek AI 分析
            ├── ocr_service.py   # Kimi 视觉 OCR
            └── health_service.py # 健康业务编排
```

---

## API 概览（24 个接口）

### 用户档案
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users/default` | 获取/创建默认用户 |
| GET | `/api/users/{id}` | 获取用户 |
| PUT | `/api/users/{id}` | 更新用户 |
| POST | `/api/users` | 创建用户 |

### 健康指标
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health/indicators` | 指标列表（支持筛选） |
| POST | `/api/health/indicators` | 添加指标（自动规则评估） |
| POST | `/api/health/indicators/batch` | 批量添加 |
| GET | `/api/health/indicators/{id}` | 指标详情 |
| PUT | `/api/health/indicators/{id}` | 更新指标（重新评估） |
| DELETE | `/api/health/indicators/{id}` | 删除指标 |
| GET | `/api/health/categories` | 指标分类列表 |
| GET | `/api/health/risk-summary` | 风险评估摘要 |
| GET | `/api/health/suggestions` | 四维度健康建议 |
| POST | `/api/health/ai-analyze` | AI 综合分析 |

### AI 健康咨询
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/chat/sessions` | 会话列表 |
| POST | `/api/chat/sessions` | 创建会话 |
| DELETE | `/api/chat/sessions/{id}` | 删除会话 |
| GET | `/api/chat/sessions/{id}/messages` | 消息历史 |
| POST | `/api/chat/send` | 发送消息（AI 回复） |

### OCR 识别
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ocr/recognize` | 上传体检报告识别 |

### 医学影像分类
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/classify/skin` | 常见皮肤状况图片初筛 |
| GET | `/api/classify/classes` | 分类类别列表 |
| GET | `/api/classify/status` | 模型、许可与运行时状态 |

模型来源、快速训练子集与验收要求见 [皮肤病变模型与训练资源](docs/模型训练资源.md)。

---

## 数据库配置

当前使用 MySQL，连接信息：

| 项目 | 值 |
|------|-----|
| 地址 | `localhost:3306` |
| 数据库 | `health` |
| 用户 | `root` |
| 密码 | `root` |

如需切换回 SQLite（开发调试），修改 `.env`：
```env
DATABASE_URL=sqlite:///./health.db
```

---

## 功能状态

| 功能 | 依赖 | 状态 |
|------|------|------|
| 用户档案管理 | — | ✅ 完成 |
| 健康指标 CRUD | — | ✅ 完成 |
| 规则引擎（6类20项） | — | ✅ 完成 |
| 风险评估摘要 | — | ✅ 完成 |
| 四维度健康建议 | — | ✅ 完成 |
| AI 综合分析 | DeepSeek API Key | ✅ 完成（需配置） |
| AI 对话咨询 | DeepSeek API Key | ✅ 完成（需配置） |
| OCR 体检报告识别 | Kimi API Key | ✅ 完成（需配置） |
| 皮肤影像初筛 | ONNX Runtime + MobileNetV2 | ✅ 完成（10.35 MB 轻量模型） |
| 前端界面 | React + Vite + Ant Design | ✅ 完成 |
| Docker 部署 | — | 📅 规划中 |

---

## 配置说明

编辑 `backend/.env`：

```env
# 数据库
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/health?charset=utf8mb4

# AI API（不配置则仅规则引擎可用）
KIMI_API_KEY=your_kimi_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

---

*文档版本：v1.2 | 更新日期：2026-06-28*
