# 智能化健康管理系统

> **Smart Health Management System** | AI 驱动的个人健康管理平台
> OCR 体检报告识别 + 健康数据分析 + AI 健康咨询 + 皮肤影像分类

---

## 🚀 快速启动

### 一键启动（推荐）

双击项目根目录的 **`start.bat`**，自动完成 MySQL → 后端 → 前端启动。

### 手动启动

#### 1. MySQL（端口 3306）

```bat
"D:\Java\MySQL\MySQL Server 8.0\bin\mysqld.exe" --defaults-file="D:\Java\MySQL\MySQL Server 8.0\my.ini"
```

验证：
```bat
"D:\Java\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -proot -e "SELECT 1;"
```

#### 2. 后端（端口 8000）

```bat
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### 3. 前端（端口 5173）

```bat
cd frontend
npm install
npx vite --port 5173
```

### 访问地址

| 地址 | 说明 |
|------|------|
| http://localhost:5173 | **前端页面** |
| http://localhost:8000/docs | **Swagger API 文档** |
| http://localhost:8000/api/health | 后端健康检查 |

---

## 📖 文档导航

| 文档 | 位置 | 内容 |
|------|------|------|
| **产品介绍** | [docs/产品介绍_智能化健康管理系统.md](docs/产品介绍_智能化健康管理系统.md) | 功能概览、技术架构、应用场景 |
| **模型训练资源** | [docs/模型训练资源.md](docs/模型训练资源.md) | 皮肤病变模型训练与部署 |
| **API 一览** | 见本文件下方 API 章节 | 唯一维护的 API 接口清单 |

---

## 🗂️ 项目结构

```
health/
├── start.bat                  ★ 一键启动脚本
├── README.md                  ★ 本文件（统一入口）
├── docs/
│   ├── 产品介绍_智能化健康管理系统.md
│   └── 模型训练资源.md
├── scripts/                   辅助脚本（SQL、数据导入）
├── backend/                   后端（Python FastAPI）
│   ├── main.py                入口
│   ├── config.py              配置加载
│   ├── .env                   环境变量（数据库/API Key）
│   ├── requirements.txt       Python 依赖
│   ├── app/
│   │   ├── database.py        数据库连接
│   │   ├── models/            SQLAlchemy 数据模型
│   │   ├── schemas/           Pydantic 请求/响应模型
│   │   ├── routers/           API 路由
│   │   ├── services/          业务逻辑（规则引擎、AI、OCR）
│   │   └── classifier/        皮肤病变分类模型（EfficientNet-B0 / MobileNetV2）
│   ├── tests/                 测试脚本
│   ├── evaluation/            模型评估报告
│   └── training/              模型训练脚本
└── frontend/                  前端（React + Vite + Ant Design + ECharts）
    ├── package.json
    ├── vite.config.js         含 API 代理（/api → :8000）
    └── src/
        ├── main.jsx
        ├── pages/             Dashboard / Health / Chat / OCR / Classify / Assessment
        ├── components/
        └── api/index.js       axios 封装
```

---

## ⚙️ 配置

### 环境要求

| 依赖 | 版本 | 位置 |
|------|------|------|
| Python | >= 3.11 | 默认安装 |
| Node.js | >= 18 | 默认安装 |
| MySQL | 8.0 | `D:\Java\MySQL\MySQL Server 8.0` |

### 数据库

| 项目 | 值 |
|------|-----|
| 地址 | `localhost:3306` |
| 数据库 | `health` |
| 用户 / 密码 | |

### `backend/.env`

```env
# 数据库（已切换为 MySQL；如需 SQLite 改 sqlite:///./health.db）
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/health?charset=utf8mb4

# AI API Key（不配置则仅规则引擎可用）
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

DeepSeek 同时承担：
- **OCR 体检报告识别**（视觉模型 `deepseek-flash`）
- **AI 健康分析 / AI 健康咨询**（文本模型 `deepseek-chat`）
- 不配 Key → OCR 和 AI 功能会返回提示，但指标录入、规则评估、健康看板正常运行

---

## 🧩 功能一览

| 功能 | 依赖 | 状态 |
|------|------|------|
| 用户档案管理 | — | ✅ |
| 健康指标 CRUD | — | ✅ |
| **规则引擎（10 类 47 项）** | — | ✅ |
| 风险评估摘要 + 分类汇总 | — | ✅ |
| 四维度健康建议（饮食/运动/作息/就医） | — | ✅ |
| AI 综合分析 | DeepSeek API Key | ✅ |
| AI 对话咨询（含会话管理） | DeepSeek API Key | ✅ |
| OCR 体检报告识别（自动保存指标） | DeepSeek API Key | ✅ |
| 皮肤影像初筛（15 类，纯本地 ONNX） | ONNX Runtime | ✅ |
| 健康数据图表（趋势/环形/交互） | — | ✅ |
| Docker 部署 | — | 📅 规划中 |

### 规则引擎覆盖（10 类 47 项）

| 分类 | 指标数 | 示例 |
|------|--------|------|
| 血糖 | 4 | 空腹血糖、餐后 2h 血糖、糖化血红蛋白、随机血糖 |
| 血压 | 2 | 收缩压、舒张压 |
| 血脂 | 7 | 总胆固醇、甘油三酯、HDL、LDL、载脂蛋白 A1/B、脂蛋白 a |
| 肝功能 | 8 | ALT、AST、总胆红素、直接胆红素、ALP、TP、ALB、TBA |
| 肾功能 | 3 | 肌酐、尿素氮、尿酸 |
| 血常规 | 4 | 白细胞、红细胞、血红蛋白、血小板 |
| 甲状腺功能 | 5 | TSH、FT3、FT4、TT3、TT4 |
| 电解质 | 6 | 钾、钠、氯、钙、磷、镁 |
| 心血管 / 心肌酶 | 4 | CK、CK-MB、LDH、超敏 CRP |
| 肿瘤标志物 | 4 | AFP、CEA、CA125、CA19-9 |
| **合计** | **47** | |

### 健康指标图表视图

- **分类环形图**：按分类展示 normal / medium / high 比例
- **指标趋势图**：折线（多日）/ 柱状（单日）自适应，带日期范围筛选（7d / 30d / 90d / 全部）和分类筛选
- **交互**：点击折线或 legend 聚焦单个指标，显示正常范围 markArea + tooltip 含正常范围与偏高/偏低判定

---

## 🔌 API 接口（24 个）

### 用户档案 `/api/users`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users/default` | 获取 / 创建默认用户 |
| GET | `/api/users/{id}` | 获取用户 |
| PUT | `/api/users/{id}` | 更新用户 |
| POST | `/api/users` | 创建用户 |

### 健康指标 `/api/health`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health/indicators` | 列表（支持分类 / 状态筛选） |
| POST | `/api/health/indicators` | 创建（自动规则评估） |
| POST | `/api/health/indicators/batch` | 批量创建 |
| GET | `/api/health/indicators/{id}` | 详情 |
| PUT | `/api/health/indicators/{id}` | 更新（自动重新评估） |
| DELETE | `/api/health/indicators/{id}` | 删除 |
| GET | `/api/health/categories` | 分类列表 |
| GET | `/api/health/risk-summary` | 风险评估摘要 + 分类汇总 |
| GET | `/api/health/suggestions` | 四维度健康建议 |
| POST | `/api/health/ai-analyze` | AI 综合分析 |
| GET | `/api/health/ai-analyses` | 已保存的 AI 分析记录 |

### AI 健康咨询 `/api/chat`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/chat/sessions` | 会话列表 |
| POST | `/api/chat/sessions` | 创建会话 |
| DELETE | `/api/chat/sessions/{id}` | 删除会话 |
| GET | `/api/chat/sessions/{id}/messages` | 消息历史 |
| POST | `/api/chat/send` | 发送消息 + AI 回复 |

### OCR `/api/ocr`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ocr/recognize` | 上传体检报告 → 自动 OCR + 保存指标 |

### 医学影像 `/api/classify`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/classify/skin` | 皮肤病变分类（纯本地 ONNX） |
| GET | `/api/classify/classes` | 支持类别列表 |
| GET | `/api/classify/status` | 模型 / 依赖状态 |

---

## 🛠️ 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | 0.138 |
| Python | CPython | 3.14 |
| 数据库 | MySQL | 8.0.41 |
| ORM | SQLAlchemy | 2.0 |
| 前端 | React + Vite + Ant Design | — |
| 图表 | ECharts | — |
| OCR / AI | DeepSeek | `deepseek-flash`(视觉) + `deepseek-chat`(文本) |
| 影像分类 | PyTorch + ONNX Runtime | EfficientNet-B0 / MobileNetV2 |

---

## 📊 开发状态

| 阶段 | 状态 |
|------|------|
| 需求分析 | ✅ |
| 技术选型 | ✅ |
| 后端基础框架 | ✅ |
| 用户档案模块 | ✅ |
| 健康指标模块 | ✅ |
| 规则引擎（10 类 47 项） | ✅ |
| 风险评估 / 健康建议 | ✅ |
| AI 咨询 / OCR | ✅ |
| 皮肤影像初筛（15 类） | ✅ |
| 前端界面 + 图表 | ✅ |
| Docker 部署 | 📅 规划中 |
| 用户权限系统 | 📅 规划中 |

### 已知问题

1. **MySQL 未注册 Windows 服务** — 开机后需手动启动，或走 `start.bat`
2. **无 AI 降级体验** — 未配 API Key 时 AI 功能返回提示，核心规则引擎不受影响
3. **端口冲突** — 8000 / 3306 被占用时需修改配置

### 待办

- Chat 流式回复
- 多用户权限系统
- Docker 容器化 + HTTPS

---

## 📄 免责声明

> **本系统提供的所有健康信息仅供参考，不构成医疗诊断或治疗方案。**
> AI 不得给出明确疾病诊断、不得开具医疗处方、不得替代医生结论。如有健康问题，请及时就医。

---

*文档版本：v2.0 | 更新日期：2026-09-20 | 仓库：https://github.com/gbdw7575-maker/---*
