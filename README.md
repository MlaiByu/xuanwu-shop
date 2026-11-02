# 玄武商城（Xuanwu Shop）

一个前后端分离的 **B2C 单商家自营商城 MVP**（形态对标京东），覆盖「浏览 → 加购 → 下单 → 管理」完整闭环。后端 FastAPI + PostgreSQL，前端 Vue 3；业务口径、接口契约、代码审查结论均沉淀在 `docs/`，可被自动化验证。

> 范围边界见 `docs/PRD.md`：**做** 商品浏览/搜索、SPU+SKU 多规格、购物车、下单（模拟支付）、订单管理、收货地址、超时自动取消/自动确认、后台商品/分类/订单管理、图片上传、JWT 鉴权。**不做** 真实支付、退款售后、优惠券、评价、物流轨迹、多商家、推荐算法等。

---

## 一、功能与角色

### 角色矩阵（四层 + 游客）

| 角色 | `role` 值 | 权限 |
|---|---|---|
| 游客 | — | 浏览、搜索、看详情 |
| 买家（C 端） | `customer` | 购物全流程 + 收货地址 |
| 商家（B 端） | `merchant` | 商品管理、上下架、我的订单（需入驻审核通过） |
| 管理员（A 端） | `admin` | 商品/分类/订单管理、发货、图片上传 |
| 超级管理员 | `super_admin` | 管理员管理 + 商家入驻审核（超管独占） |

### 核心业务能力

- **商品**：多级分类（≤3 级，防成环）、SPU+SKU 多规格、关键词搜索（转义通配符）、价格/库存筛选、销量排序
- **购物车**：游客本地加购、登录后自动并入服务端、库存实时校验、失效标记
- **下单**：幂等（`ON CONFLICT DO NOTHING`）、条件更新扣库存防超卖、地址快照、订单号由自增 id 派生
- **订单状态机**：`pending → paid → shipped → completed`，`pending → cancelled`（手动/超时），全程条件更新保证幂等
- **支付**：模拟支付（`POST /orders/{id}/pay` 直接改状态，无真实网关）
- **后台任务**：订单超时自动取消（回滚库存）、发货超时自动确认收货
- **智能客服**：LangGraph 状态图驱动，查订单/物流/商品/政策 + 转人工工单，SSE 流式

### 智能客服（LangGraph）

C 端右下角「客服小玄」，按「分类 → 查事实 → 生成 → 转人工」的状态图运行。

- **图结构**：`classify` → 条件边分流到 `query_order` / `query_logistics` / `search_product` / `retrieve_policy` → `generate` → 命中人工条件走 `handoff`。用图而不是链，是因为四类查询互斥，且存在「查不到 → 转人工」的回退路径，链式编排表达不了。
- **事实与措辞分离**：订单、金额、库存、政策条文全部由工具和静态知识库产出，模型只组织语言；模型故障自动降级为内置规则话术（`mode=rule`），客服不会失联。
- **越权防护**：订单查询强制 `user_id + order_no` 双条件，单号猜对了也查不到别人的单；工具只读，退款/改地址/赔偿一律转人工。
- **转人工**：投诉与情绪词、政策未命中、模型无把握时写入 `support_tickets` 并回传工单号。
- **流式**：`POST /api/v1/support/chat` 返回 SSE，事件 `meta / intent / tool / policy / token / handoff / done`，前端按 token 做打字机。
- **会话**：暂存内存（单机演示），换 Redis 或落表即可，事件协议不变。
- **可选模型**：`SUPPORT_LLM_API_KEY` 留空走规则引擎；填任意 OpenAI 兼容服务的 Key（DeepSeek / 通义 / OpenAI）即切真实模型，代码零改动。

---

## 二、技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI 0.115 · SQLAlchemy 2.0 · Alembic · Pydantic v2 · PyJWT · bcrypt · psycopg3 |
| 数据库 | PostgreSQL（16+，开发环境实测 18.6） |
| 前端 | Vue 3.5 · Vite 6 · Element Plus · Pinia · Vue Router 4 · axios（纯 JavaScript，无 TS） |
| 运行时 | Python 3.12 / Node.js 18+ |

---

## 三、项目结构

```
xuanwu/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # 路由层：auth / categories / products / cart / addresses
│   │   │   │                 #        / orders / merchant / support
│   │   │   │                 #        + admin/（商品、分类、订单、上传、商家审核、管理员）
│   │   │   └── deps.py       # 依赖注入：四层鉴权（get_current_user/admin/super_admin/merchant）
│   │   ├── schemas/          # Pydantic 请求/响应模型（入参校验）
│   │   ├── services/         # 业务逻辑与事务（下单、库存、状态机、认证…）
│   │   ├── support/          # 智能客服：LangGraph 图 / 工具 / 政策库 / LLM 适配 / SSE 编排
│   │   ├── repositories/     # 数据访问（UserRepository）
│   │   ├── models/           # SQLAlchemy ORM
│   │   ├── core/             # security(JWT/bcrypt) / errors(错误码) / logging / scheduler / money
│   │   ├── config.py         # 环境变量（pydantic-settings）
│   │   └── main.py           # FastAPI 入口（CORS、异常处理器、静态挂载、调度器）
│   ├── alembic/              # 数据库迁移（PostgreSQL）
│   ├── scripts/              # seed_demo / create_admin / expand_catalog
│   ├── requirements.txt / pyproject.toml（ruff·mypy·pyright 配置）
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── views/            # C 端 store 视图 + admin/ + merchant/ 管理视图
│   │   ├── components/       # 通用组件 + store/ 门店组件
│   │   ├── store/            # Pinia：user / cart
│   │   ├── api/              # axios 封装 + 接口定义
│   │   ├── router/           # 路由 + 权限守卫
│   │   └── utils/            # 金额格式化等
│   └── vite.config.js        # dev 代理 /api、/static → 127.0.0.1:8000
└── docs/                     # PRD / API-CONTRACT / 代码审查报告
```

**分层约定**：请求进入 `api`（鉴权 + 参数）→ 调 `services`（业务 + 事务）→ 经 `repositories` 访问 `models`。响应统一走 `schemas` + `core/responses.py` 的信封格式。

---

## 四、快速开始

### 前置要求

- **Python 3.12**（Windows 若 `python` 被商店占位，用 `py -3.12`）
- **Node.js 18+**
- **PostgreSQL 16+**（先建空库，例如 `xuanwu`）

### 1. 后端

```bash
cd backend

python3.12 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows

cp .env.example .env          # 编辑 DATABASE_URL、JWT_SECRET_KEY

./.venv/Scripts/python.exe -m alembic upgrade head              # 建表

# 可选：灌演示数据（8 大类商品）+ 创建超管
./.venv/Scripts/python.exe -m scripts.seed_demo
./.venv/Scripts/python.exe -m scripts.create_admin <邮箱> <密码>

./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

启动后：接口文档 `http://127.0.0.1:8000/docs`（非生产）、健康检查 `http://127.0.0.1:8000/healthz`。

### 2. 前端

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173，/api、/static 已代理到 8000
```

打开 `http://localhost:5173`：游客浏览；注册/登录走完整闭环；管理端 `/admin`、商家端 `/merchant`。

---

## 五、环境变量（`backend/.env`）

| 变量 | 说明 | 默认 |
|---|---|---|
| `APP_ENV` | `dev` / `prod` | `dev` |
| `DEBUG` | 调试开关 | `true` |
| `DATABASE_URL` | PostgreSQL 连接串（**必填**） | 无 |
| `JWT_SECRET_KEY` | 签名密钥，**生产必改** | `change-me-in-production` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 凭证有效期（分钟） | `1440` |
| `CORS_ORIGINS` | 允许的跨域来源（逗号分隔） | `localhost:5173` |
| `ORDER_EXPIRE_JOB_ENABLED` | 是否开启订单超时任务 | `false` |
| `ORDER_EXPIRE_MINUTES` / `ORDER_AUTO_CONFIRM_DAYS` | 超时取消 / 自动确认时长 | `30` / `15` |

> `APP_ENV=prod` 时：使用默认 `JWT_SECRET_KEY` 会**直接拒绝启动**；`/docs` 关闭；认证 cookie 自动加 `Secure`。

---

## 六、响应结构与错误码

所有接口（含错误）统一信封：

```json
{ "code": 0, "message": "ok", "data": {} }
```

铁律：`HTTP 2xx ⟺ code == 0`，不允许「HTTP 200 + 业务错误码」。

| code | HTTP | 含义 |
|---|---|---|
| `0` | 200 | 成功 |
| `40001` | 400 | 参数校验失败 |
| `40002` | 400 | 参数逻辑冲突 |
| `40100` | 401 | 未登录 |
| `40101` | 401 | 凭证无效或已过期 |
| `40300` | 403 | 权限不足 |
| `40400` | 404 | 资源不存在（归属校验失败也用它，防枚举） |
| `40900` | 409 | 资源已存在 |
| `40901` | 409 | 库存不足 |
| `40902` | 409 | 当前状态不支持该操作 |
| `40903` | 409 | 重复提交（幂等键冲突） |
| `50000` | 500 | 服务器内部错误 |

完整字段级契约见 `docs/API-CONTRACT.md`（权威性高于 PRD）。

---

## 七、认证

- 登录 `POST /api/v1/auth/login` 成功后，凭证以 **httpOnly cookie**（`access_token`）下发，前端 JS 读不到、XSS 窃取不了。
- Cookie 属性：`HttpOnly; SameSite=Lax; Path=/`（生产 HTTPS 自动加 `Secure`）。
- 后端同时兼容 `Authorization: Bearer <token>`（curl / 脚本调试用）。
- 改密、封禁账号会令已签发凭证**立即失效**（`token_version` 机制），需重新登录。

---

## 八、数据库与迁移

- 仅支持 PostgreSQL，连接串由 `DATABASE_URL` 注入，缺省会启动失败。
- Alembic 管理 schema：

```bash
./.venv/Scripts/python.exe -m alembic upgrade head   # 升级到最新
./.venv/Scripts/python.exe -m alembic current        # 查看当前版本
./.venv/Scripts/python.exe -m alembic downgrade -1   # 回退一步
```

新增字段/表请**新建迁移**（`alembic revision -m "..."`），不要改写已应用的历史迁移。

---

## 九、脚本

| 命令 | 用途 |
|---|---|
| `python -m scripts.seed_demo [--reset]` | 灌演示商品/分类；`--reset` 清空业务表重建（保留用户与地址） |
| `python -m scripts.create_admin <邮箱> <密码>` | 创建超级管理员 |
| `python -m scripts.expand_catalog` | 商品目录扩充到 100 件并指向本地静态图 |
| `python -m scripts.create_support_tables` | 创建客服工单表（幂等） |
| `python -m scripts.check_support` | 客服模块冒烟自检：意图分类 / 政策检索 / 订单号提取 |
| `python -m scripts.check_llm` | 检查客服 LLM 配置与连通性（未配 Key 时只打印当前模式） |

---

## 十、测试与质量

- 仓库当前**未内置 pytest 测试套件**；接口验收以 `docs/API-CONTRACT.md` 为口径，可在 `/docs` 手动验证。
- 代码审查结论与修复记录见 `docs/代码审查报告-2026-11-01.md`（Critical/Major/Minor 分级）。
- 工程约束：金额全程 `Decimal`（禁 float）、订单状态条件更新（天然幂等）、越权一律 404、上传校验魔数 + 分块限流。

---

## 十一、文档索引

| 文档 | 内容 |
|---|---|
| `docs/PRD.md` | 产品需求与业务口径 |
| `docs/API-CONTRACT.md` | 接口字段、类型、错误码（冲突时以它为准） |
| `docs/代码审查报告-2026-11-01.md` | 全量代码审查结论 |
