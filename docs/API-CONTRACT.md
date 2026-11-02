# 玄武商城 接口契约（API Contract）

| 项 | 内容 |
|---|---|
| 版本 | v1.0（按现有代码实测校准） |
| 基准 | 后端 `backend/app` 实现 + 运行中的 `http://127.0.0.1:8000` 实测 |
| 适用 | 前端请求封装、后端接口实现、联调排错、接口自动化 |
| 配套 | 《PRD.md》业务口径；《商品购物平台-产品需求文档-v3.0.md》归档基线 |

> **这份文档的权威性高于 PRD。** 字段名、类型、错误码以本文为准；业务意图以 PRD 为准。
> 两者冲突时，先按 §12 的差异表确认是「文档没跟上代码」还是「代码写错了」，再决定改哪边——不允许两边各写一套。

---

## 1. 通用约定

### 1.1 地址与认证

| 项 | 值 |
|---|---|
| Base URL | `http://127.0.0.1:8000`（生产替换域名） |
| 接口前缀 | `/api/v1` |
| 静态资源 | `/static/**`（上传后的图片直接可访问） |
| 认证头 | `Authorization: Bearer <token>` |
| 内容类型 | `application/json`；上传为 `multipart/form-data` |
| 交互文档 | 非生产环境 `GET /docs`（Swagger） |

### 1.2 响应结构

所有接口（含错误）返回统一信封：

```json
{ "code": 0, "message": "ok", "data": {} }
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | int | 0 成功；非 0 见 §1.3 |
| `message` | string | 面向用户的提示，可直接展示；技术细节只进日志 |
| `data` | object \| array \| null | 业务数据；删除类接口为 `null` |

**铁律**：`HTTP 2xx ⟺ code == 0`。不允许「HTTP 200 + code=40100」这种写法。

**成功状态码**：

| 场景 | HTTP |
|---|---|
| `POST /auth/register` | **201** |
| 其余全部成功（含幂等重放） | 200 |

### 1.3 错误码

| code | HTTP | 含义 | 前端该怎么做 |
|---|---|---|---|
| 0 | 200/201 | 成功 | — |
| 40001 | 400 | 参数校验失败 | 定位字段并标红，`data.errors` 里有明细 |
| 40002 | 400 | 参数逻辑冲突 | 提示具体冲突（如价格区间、时间范围） |
| 40100 | 401 | 未登录 / 账号锁定 | 清 token 跳登录；锁定文案直接展示 |
| 40101 | 401 | token 无效或过期 | 清 token 跳登录 |
| 40300 | 403 | 权限不足 / 账号停用 | 提示「无权限」；停用则提示「账号已被停用」 |
| 40400 | 404 | 资源不存在**或不属于当前用户** | 统一提示「资源不存在或已删除」，不要提示「无权限」 |
| 40900 | 409 | 资源已存在 | 提示重复（邮箱、手机号、SKU 编码、规格组合） |
| 40901 | 409 | 库存不足 | 提示并刷新库存/回退数量 |
| 40902 | 409 | 状态不可用 | 提示「当前状态不支持该操作」并刷新页面数据 |
| 40903 | 409 | 重复提交冲突 | 提示「请勿重复提交」 |
| 50000 | 500 | 服务端异常 | 通用错误提示，不展示细节 |

**校验失败时 `data` 结构**：

```json
{ "code": 40001, "message": "参数校验失败",
  "data": { "errors": [{ "field": "email", "reason": "value is not a valid email address" }] } }
```

### 1.4 分页

请求：`page`（默认 1，≥1）、`size`（默认 20，1–100）。

响应 `data`：

```json
{ "items": [], "total": 137, "page": 1, "size": 20, "pages": 7 }
```

| 边界 | 行为 |
|---|---|
| `page` 超总页数 | 200，`items=[]`，`total`/`pages` 保持真实值 |
| `page=0` | 400 / 40001 |
| `size=0` | 400 / 40001 |
| `size=101` | 400 / 40001（Pydantic 拦截，不是 40002） |
| `total=0` | `pages=0`（不是 1） |

### 1.5 金额

**一律是字符串，两位小数，不带货币符号。**

| 位置 | 示例 |
|---|---|
| `price` / `total_amount` / `subtotal` | `"129.00"` |
| 请求里传价格（管理端） | 传 `"129.00"` 或 `129.0` 均可，后端转 Decimal 并量化到 2 位 |

前端禁止用 JS `Number` 做累加，展示用 `formatPrice()`，计算用 big.js。

### 1.6 时间

| 项 | 说明 |
|---|---|
| 格式 | ISO 8601，如 `2026-10-29T11:33:27` |
| 时区 | **现状不统一**：`UserOut.created_at` 会补 UTC 偏移（`+00:00`）；商品、分类、订单等接口返回的时间**不带偏移**（SQLite 不存时区），按 UTC 解析 |
| 入库参数 | 管理端时间筛选接受 `YYYY-MM-DDTHH:mm:ss` 或 `YYYY-MM-DD HH:mm:ss` |
| 前端处理 | 统一 `dayjs.utc(t).local()` 展示，不要直接 `new Date(str)` 后按本地时区理解 |

> 这是当前实现的真实情况，不是设计目标。切 PostgreSQL（`TIMESTAMPTZ`）后偏移会正常，但前端按 UTC 解析的写法在两种环境下都对——所以按 UTC 写。

### 1.7 幂等

仅 `POST /orders` 支持，请求头 `Idempotency-Key: <UUID>`。

| 场景 | 结果 |
|---|---|
| 同用户 + 同 key + 同请求体 | 200，返回首次创建的订单（不重复下单、不重复扣库存） |
| 同用户 + 同 key + 不同请求体 | 409 / 40903 |
| 不带该头 | 正常下单；重复提交由前端按钮禁用兜底 |

请求体摘要对 `cart_item_ids` 做了排序后比对，因此顺序不同视为「同请求体」。

**其余状态变更接口不靠幂等键**，而是条件更新天然幂等：重复调用返回 40902，不会二次扣减/回滚。

### 1.8 权限层级

| 层级 | 校验 | 失败返回 |
|---|---|---|
| L1 认证 | 有 token 且有效 | 40100 / 40101 |
| L2 角色 | 管理端要求 `is_admin=true` | 40300 |
| L3 归属 | 资源 `user_id == 当前用户` | **40400**（不是 40300） |
| L4 状态 | 当前状态允许该操作 | 40902 |

**带资源 id 的接口全部要过 L3**：订单、购物车项、地址、结算项。

---

## 2. 接口总览

| # | 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|---|
| 1 | POST | `/auth/register` | 否 | 注册（201） |
| 2 | POST | `/auth/login` | 否 | 登录 |
| 3 | GET | `/auth/me` | 用户 | 当前用户 |
| 4 | GET | `/categories` | 否 | 分类树 |
| 5 | GET | `/products` | 否 | 商品列表 |
| 6 | GET | `/products/{id}` | 否 | 商品详情 |
| 7 | GET | `/cart` | 用户 | 购物车 |
| 8 | POST | `/cart` | 用户 | 加购 |
| 9 | PATCH | `/cart/{id}` | 用户 | 改数量 |
| 10 | DELETE | `/cart/{id}` | 用户 | 删除项 |
| 11 | GET | `/addresses` | 用户 | 地址列表 |
| 12 | POST | `/addresses` | 用户 | 新增地址 |
| 13 | PUT | `/addresses/{id}` | 用户 | 编辑地址 |
| 14 | DELETE | `/addresses/{id}` | 用户 | 删除地址 |
| 15 | PATCH | `/addresses/{id}/default` | 用户 | 设为默认 |
| 16 | GET | `/orders/checkout` | 用户 | 结算预览 |
| 17 | POST | `/orders` | 用户 | 提交订单 |
| 18 | GET | `/orders` | 用户 | 我的订单 |
| 19 | GET | `/orders/{id}` | 用户 | 订单详情 |
| 20 | POST | `/orders/{id}/pay` | 用户 | 模拟支付 |
| 21 | POST | `/orders/{id}/cancel` | 用户 | 取消 |
| 22 | POST | `/orders/{id}/confirm` | 用户 | 确认收货 |
| 23 | GET | `/admin/ping` | 管理员 | 管理端连通性检查 |
| 24 | GET | `/admin/products` | 管理员 | 商品列表 |
| 25 | POST | `/admin/products` | 管理员 | 新增商品 |
| 26 | GET | `/admin/products/{id}` | 管理员 | 商品详情 |
| 27 | PUT | `/admin/products/{id}` | 管理员 | 编辑商品 |
| 28 | DELETE | `/admin/products/{id}` | 管理员 | 删除商品 |
| 29 | PATCH | `/admin/products/{id}/status` | 管理员 | 上下架 |
| 30 | GET | `/admin/categories` | 管理员 | 分类树 |
| 31 | POST | `/admin/categories` | 管理员 | 新增分类 |
| 32 | PUT | `/admin/categories/{id}` | 管理员 | 编辑分类 |
| 33 | DELETE | `/admin/categories/{id}` | 管理员 | 删除分类 |
| 34 | GET | `/admin/orders` | 管理员 | 订单列表 |
| 35 | POST | `/admin/orders/{id}/ship` | 管理员 | 发货 |
| 36 | POST | `/admin/orders/{id}/expire` | 管理员 | 触发超时取消（**仅非生产**） |
| 37 | POST | `/admin/upload` | 管理员 | 上传图片 |
| 38 | GET | `/healthz` | 否 | 健康检查（无前缀） |

---

## 3. 认证

### 3.1 POST /auth/register

**请求**

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `email` | string | 是 | 邮箱格式，≤120；存储转小写 |
| `phone` | string\|null | 否 | `^1[3-9]\d{9}$`；空串按 null 处理 |
| `password` | string | 是 | 8–64 位，须同时含字母与数字 |
| `nickname` | string\|null | 否 | ≤20；不传则取邮箱前缀（超 20 截断） |

```json
{"email":"a@b.com","phone":"13800138000","password":"Passw0rd123","nickname":"小明"}
```

**响应 201**

```json
{"code":0,"message":"ok","data":{"id":1,"email":"a@b.com","phone":"13800138000",
"nickname":"小明","is_admin":false,"created_at":"2026-10-29T11:33:27+00:00"}}
```

**错误**：40001（格式/强度）、40900（邮箱或手机号已存在）

> 响应**不含** `hashed_password`，这是硬要求。

### 3.2 POST /auth/login

**请求**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `account` | string | 是 | 邮箱或手机号，1–120 |
| `password` | string | 是 | 1–64 |

**响应 200**

```json
{"code":0,"message":"ok","data":{"token":"eyJ...","expires_in":86400,
"user":{"id":1,"email":"a@b.com","phone":null,"nickname":"a","is_admin":false,"created_at":"..."}}}
```

**错误**

| 场景 | code | message |
|---|---|---|
| 参数缺失 | 40001 | 参数校验失败 |
| 账号不存在 / 密码错误 | 40100 | 账号或密码错误（**两者文案必须一致**） |
| 5 分钟内失败 5 次 | 40100 | 尝试过于频繁，请 N 分钟后重试 |
| 账号被停用 | 40300 | 账号已被停用 |

### 3.3 GET /auth/me

响应 `data` 为 `UserOut`。无 token → 40100；token 失效 → 40101。

---

## 4. 分类

### 4.1 GET /categories

无参数，返回整棵树（已按 `sort ASC, id ASC` 排好）。

```json
{"code":0,"message":"ok","data":[
  {"id":1,"name":"电子","parent_id":null,"level":1,"sort":1,
   "children":[{"id":2,"name":"手机","parent_id":1,"level":2,"sort":1,"children":[]}]}
]}
```

`CategoryOut` 字段：`id` / `name` / `parent_id` / `level`(1–3) / `sort` / `children[]`。

---

## 5. 商品

### 5.1 GET /products

**Query**

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `category_id` | int | — | 含该分类的全部子孙分类 |
| `keyword` | string | — | ≤50，对商品名 `ILIKE`，首尾空格自动 trim，`%`/`_` 已转义 |
| `min_price` | string | — | 按**最低 SKU 价**过滤，含边界 |
| `max_price` | string | — | 同上 |
| `sort` | enum | `default` | `default` / `sales_desc` / `price_asc` / `price_desc` |
| `page` / `size` | int | 1 / 20 | 见 §1.4 |

**排序实现**

| sort | 实际排序 |
|---|---|
| `default` | `sales_count DESC, id DESC` |
| `sales_desc` | 同 default |
| `price_asc` | 最低 SKU 价 ASC, id DESC |
| `price_desc` | 最低 SKU 价 DESC, id DESC |

**响应 `data`**：`Page<ProductListItem>`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | — |
| `name` | string | — |
| `main_image` | string | 相对路径或外链 |
| `category_id` | int | — |
| `price` | string | **最低 SKU 价**（仅统计启用中的 SKU） |
| `max_price` | string | 最高 SKU 价 |
| `sales_count` | int | 销量 |
| `has_stock` | bool | 总库存 > 0 |

> **注意**：`has_stock=false` 的商品**仍会返回**，前端需自行决定展示「暂时缺货」还是过滤（见 PRD Q1）。

**错误**：40001（参数格式/长度）、40002（`min_price > max_price`）

### 5.2 GET /products/{id}

**响应 `data`**：`ProductDetail`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` / `name` / `description` | — | `description` 可为 null |
| `main_image` | string | — |
| `images` | string[] | 图集，可为空数组 |
| `category_id` | int | — |
| `sales_count` | int | — |
| `price_range` | `{min, max}` | 均为字符串 |
| `spec_keys` | string[] | 规格键，如 `["颜色","尺寸"]`，按 SKU 出现顺序去重 |
| `skus` | `SkuOut[]` | 见下 |

`SkuOut`：`id` / `sku_code` / `attrs`(object) / `price`(string) / `stock`(int) / `is_active`(bool)

```json
{"code":0,"message":"ok","data":{"id":12,"name":"纯棉T恤","description":null,
"main_image":"/static/uploads/2026/10/ab.png","images":[],"category_id":3,"sales_count":8,
"price_range":{"min":"59.00","max":"79.00"},"spec_keys":["颜色","尺寸"],
"skus":[{"id":31,"sku_code":"TS-RED-L","attrs":{"颜色":"红","尺寸":"L"},"price":"59.00","stock":8,"is_active":true}]}}
```

**错误**：40400（不存在 / 已下架 / 无可用规格）

---

## 6. 购物车

### 6.1 GET /cart

**响应 `data`**：`CartSummary`

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | `CartItemOut[]` | 按 id 升序 |
| `total_quantity` | int | **仅统计 `is_valid=true` 的件数** |
| `total_amount` | string | 仅统计有效项金额 |

`CartItemOut`：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 购物车项 id（结算用它） |
| `sku_id` / `product_id` | int | — |
| `product_name` / `main_image` | string | 实时，非快照 |
| `attrs` | object | SKU 规格 |
| `price` | string | 实时单价 |
| `quantity` | int | 1–999 |
| `stock` | int | 当前库存 |
| `is_valid` | bool | 下架 / SKU 停用 / 库存为 0 时为 false |
| `subtotal` | string | `price × quantity` |

> `is_valid` 的判定**不含**「数量是否超过库存」——数量超过库存仍为 valid，但结算时会被拦。

### 6.2 POST /cart

**请求**：`{"sku_id": 31, "quantity": 2}`，`quantity` 1–999。

**响应 `data`**：`CartItemOut`（累加后的最新状态）

**错误**

| 场景 | code | message |
|---|---|---|
| 数量越界/类型错 | 40001 | 参数校验失败 |
| 累加后超库存 | 40901 | 库存不足（**原记录不变**） |
| SKU 不存在 / 已停用 | 40902 | 商品规格不存在或已下架 |
| 商品已下架 | 40902 | 商品已下架 |

> 注意：**SKU 不存在返回 40902，不是 404**。前端判断「商品没了」要同时处理 40400 和 40902。

### 6.3 PATCH /cart/{id}

**请求**：`{"quantity": 3}`（覆盖语义，非增量）

**响应**：`CartItemOut`。错误：40001 / 40400（不存在或非本人）/ 40901（超库存）/ 40902（SKU 已失效）

### 6.4 DELETE /cart/{id}

**响应**：`data: null`。错误：40400。

---

## 7. 收货地址

`AddressOut`（前端实际只用这些字段）：`id` / `receiver` / `phone` / `province` / `city` / `district` / `detail` / `is_default`

| 方法 | 路径 | 请求体 | 响应 |
|---|---|---|---|
| GET | `/addresses` | — | 地址数组（默认地址排最前，**不分页**） |
| POST | `/addresses` | 全字段 | 新建的地址对象 |
| PUT | `/addresses/{id}` | 全字段（覆盖） | 更新后的地址对象 |
| DELETE | `/addresses/{id}` | — | `null` |
| PATCH | `/addresses/{id}/default` | — | 更新后的地址对象 |

> **注意**：地址类接口返回的是 ORM 裸对象，除上表字段外还**多出 `user_id`、`created_at`、`updated_at`**（实测）。前端只用自己需要的字段即可，不要依赖 `user_id`（见 §12 D-13）。

**字段约束**

| 字段 | 约束 |
|---|---|
| `receiver` | 1–20 |
| `phone` | `^1[3-9]\d{9}$` |
| `province` / `city` / `district` | 1–50，必填 |
| `detail` | **5–200** |
| `is_default` | bool，默认 false；第一个地址服务端强制为 true |

**错误**：40001（格式）、40400（不存在或非本人）

> `PUT` 是**全量覆盖**：没传的字段会被置空/校验失败，前端编辑时必须回填完整对象。

---

## 8. 订单

### 8.1 GET /orders/checkout

**Query**

| 参数 | 必填 | 说明 |
|---|---|---|
| `cart_item_ids` | 是 | 逗号分隔，如 `1,2,3`；允许空串 |

**响应 `data`**：`CheckoutPreview`

| 字段 | 类型 | 说明 |
|---|---|---|
| `address` | object\|null | 默认地址；无地址为 null |
| `items` | `CheckoutItem[]` | 含 `is_valid` 标记 |
| `total_quantity` | int | 有效项件数 |
| `total_amount` | string | 有效项金额 |
| `freight` | string | 固定 `"0.00"` |

`CheckoutItem`：`cart_item_id` / `product_name` / `sku_attrs` / `main_image` / `price` / `quantity` / `subtotal` / `is_valid`

**错误**

| 场景 | code |
|---|---|
| 缺 `cart_item_ids` 参数 | 40001 |
| 某些 id 不存在或不属于当前用户 | 40400「部分购物车项不存在」 |

> **空串 `cart_item_ids=` 返回 200 + 空预览**，不是 400。前端应拦截「没选商品不进结算页」。

### 8.2 POST /orders

**请求头**：`Idempotency-Key: <UUID>`（可选）

**请求体**

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `address_id` | int | 是 | 须属于当前用户 |
| `cart_item_ids` | int[] | 是 | 至少 1 个 |
| `remark` | string\|null | 否 | ≤200 |

**响应 200**

```json
{"code":0,"message":"ok","data":{"id":7,"order_no":"20261029113327604216",
"status":"pending","total_amount":"129.00"}}
```

**错误**

| 场景 | code | message |
|---|---|---|
| 参数缺失 / 空数组 / 备注超长 | 40001 | 参数校验失败 |
| 地址不存在或非本人 | 40400 | 收货地址不存在 |
| 购物车项不存在或非本人 | 40400 | 部分购物车项不存在 |
| 商品/规格已下架 | 40902 | 商品已下架：xxx |
| 库存不足（任一 SKU） | 40901 | 库存不足：SKU-CODE（**整单回滚**） |
| 同 key 不同请求体 | 40903 | 相同幂等键携带了不同的请求 |

**事务内顺序**（排查问题时按这个顺序看日志）：
地址归属 → 购物车项归属 → 商品在售 → 按 `sku_id` 升序条件扣减 → 建单与快照 → 清购物车 → 落幂等键。

### 8.3 GET /orders

**Query**：`status`（`all` 默认 / `pending` / `paid` / `shipped` / `completed` / `cancelled`，非法值 40001）、`page`、`size`

**响应**：`Page<OrderListItem>`

`OrderListItem`：`id` / `order_no` / `status` / `total_amount` / `created_at` / `total_quantity` / `preview_image` / `preview_name`

> `preview_image` / `preview_name` 取第一件商品，可能为 null。

### 8.4 GET /orders/{id}

**响应 `data`**：`OrderDetail`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` / `order_no` / `status` | — | — |
| `total_amount` | string | — |
| `remark` | string\|null | — |
| `created_at` | string | — |
| `address_snapshot` | object | `receiver`/`phone`/`province`/`city`/`district`/`detail`，**下单时快照** |
| `items` | `OrderItemOut[]` | 见下 |
| `timeline` | `{label, time}[]` | 已发生节点，按时间正序 |

`OrderItemOut`：`id` / `product_name` / `sku_attrs` / `main_image` / `price` / `quantity` / `subtotal`
（均为下单时快照，商品改价改名不影响）

`timeline.label` 取值：`下单` / `支付成功` / `已发货` / `交易完成` / `已取消`

**错误**：40400（不存在或非本人）

### 8.5 状态流转

| 方法 | 路径 | 前置状态 | 成功后 |
|---|---|---|---|
| POST | `/orders/{id}/pay` | `pending` | `paid`，累加销量 |
| POST | `/orders/{id}/cancel` | `pending` | `cancelled`，回滚库存 |
| POST | `/orders/{id}/confirm` | `shipped` | `completed` |

响应统一：`{"id": 7, "status": "paid"}`

**错误**

| 场景 | code | message |
|---|---|---|
| 非本人 / 不存在 | 40400 | 资源不存在 |
| 状态不满足（含重复调用） | 40902 | 仅待支付订单可支付（文案随动作变化） |

> 重复支付/取消返回 40902 是**正确行为**，前端不要当网络错误重试。

---

## 9. 管理端

### 9.1 GET /admin/ping

连通性与身份检查，用于前端判断「是否已用管理员身份登录」：

```json
{"code":0,"message":"ok","data":{"admin_id":3,"email":"admin@example.com"}}
```

非管理员调用 → 40300。

### 9.2 GET /admin/products

**Query**：`keyword`（≤50）、`category_id`、`is_active`(bool)、`page`、`size`

**响应**：`Page<ProductAdminItem>`

`ProductAdminItem` = `ProductListItem` 全部字段 +：

| 字段 | 类型 | 说明 |
|---|---|---|
| `description` | string\|null | — |
| `is_active` | bool | 上下架状态 |
| `sku_count` | int | SKU 数量 |
| `skus` | `SkuOut[]` | 完整 SKU 列表（含停用） |

排序：`id DESC`（最新在前）。

### 9.3 POST /admin/products

**请求**

```json
{"name":"纯棉T恤","category_id":3,"description":"","main_image":"/static/uploads/...png",
 "images":["/static/uploads/...png"],"is_active":true,
 "skus":[{"sku_code":"TS-RED-L","attrs":{"颜色":"红","尺寸":"L"},"price":"59.00","stock":10,"is_active":true}]}
```

| 字段 | 约束 |
|---|---|
| `name` | 1–200 |
| `category_id` | 必须存在 |
| `main_image` | 1–500，必填 |
| `images` | string[]，可空 |
| `skus` | **至少 1 个** |
| `skus[].attrs` | 非空对象，键值都非空 |
| `skus[].price` | ≥0，两位小数 |
| `skus[].stock` | ≥0 整数 |

**响应 200（注意）**

```json
{"code":0,"message":"ok","data":{"id":34,"name":"...","description":null,"images":[],
"sales_count":0,"main_image":"...","category_id":1,"is_active":false,
"created_at":"2026-10-29T11:40:25","updated_at":"2026-10-29T11:40:25"}}
```

> **返回的是商品主体，不含 `skus`、不含价格区间。** 前端创建成功后要重新 `GET /admin/products/{id}` 拿完整数据，不能直接把这个响应塞进列表。

**错误**

| 场景 | code |
|---|---|
| 字段非法 / SKU 为空 | 40001 |
| SKU 规格键集合不一致 | 40001 |
| 规格组合重复 | 40900「SKU 规格组合重复」 |
| `sku_code` 已存在 | 40900「SKU 编码已存在：xxx」 |
| 分类不存在 | 40400 |

### 9.4 GET /admin/products/{id}

返回 `ProductAdminItem`（含 `skus`）。可查已下架商品。

### 9.5 PUT /admin/products/{id}

请求体同新增。**SKU 采用整体替换**：先删旧 SKU 再重建。

> 副作用：旧 SKU 被删除后，历史订单明细的 `sku_id` 会变为 NULL（快照字段仍在）。见 §13 B-01。

### 9.6 DELETE /admin/products/{id}

成功 `data: null`。有订单关联 → 40902「该商品存在历史订单，请改为下架」。

### 9.7 PATCH /admin/products/{id}/status

**请求**：`{"is_active": true}`

> 实现上读取任意 JSON 的 `is_active`，**缺省时按 true 处理**。前端必须显式传值，不要发空对象。

### 9.8 分类管理

| 方法 | 路径 | 请求体 | 响应 |
|---|---|---|---|
| GET | `/admin/categories` | — | `CategoryOut[]`（树） |
| POST | `/admin/categories` | `{name, parent_id, sort}` | 分类主体（裸对象） |
| PUT | `/admin/categories/{id}` | 同上 | 分类主体 |
| DELETE | `/admin/categories/{id}` | — | `null` |

**约束**：`name` 1–50；层级 ≤3；`parent_id` 不能是自身或后代。

**错误**：40001（长度）、40002（父分类是自身 / 成环 / 超过层级）、40400（不存在）、40902（有子分类或有商品）

> 创建/编辑分类返回的是 ORM 裸对象，**不含 `children`**；前端改完树要重新拉 `GET /admin/categories`。

### 9.9 GET /admin/orders

**Query**：`order_no`（精确）、`status`（逗号分隔多选）、`start_time`、`end_time`（作用于 `created_at`，闭区间）、`page`、`size`

**响应**：`Page<OrderListItem>`

> **现状不含收货人 / 电话**（后端定义了 `AdminOrderListItem` 但未启用）。运营要看收货信息得进详情或另行改造，见 §12 D-05。

**错误**：40001（时间格式非法）、40002（`start_time > end_time`）

### 9.10 POST /admin/orders/{id}/ship

前置 `paid`，否则 40902。响应 `{id, status:"shipped"}`。

### 9.11 POST /admin/orders/{id}/expire

**仅非生产环境**。把 `pending` 订单立即置为 `cancelled` 并回滚库存，用于测试超时逻辑（不用等 30 分钟）。生产环境返回 40400。

### 9.12 POST /admin/upload

`multipart/form-data`，字段名 `file`。

| 项 | 值 |
|---|---|
| 允许类型 | `image/jpeg` / `image/png` / `image/webp`（同时校验 Content-Type 与魔数） |
| 大小上限 | 5 MB |
| 存储 | `static/uploads/{yyyy}/{mm}/{uuid}.{ext}` |
| 响应 | `{"code":0,"message":"ok","data":{"url":"/static/uploads/2026/10/xxx.png"}}` |

**错误**：40001（类型不符 / 超 5MB / 空文件 / 魔数不符）、40300（非管理员）

---

## 10. 前端错误处理约定

| code | 全局行为 | 局部行为 |
|---|---|---|
| 40001 | 不弹全局 toast | 字段标红 + 字段级提示（用 `data.errors`） |
| 40002 | toast 提示 `message` | 定位到冲突控件（价格区间、时间范围） |
| 40100 / 40101 | 清 token → `/login?redirect=当前路径` | — |
| 40300 | toast「无权限」 | 管理端页面可跳 403 页 |
| 40400 | toast「资源不存在或已删除」 | 详情页可直接渲染 404 页 |
| 40900 | toast `message` | 表单字段标红 |
| 40901 | toast `message` | 刷新库存、回退数量输入 |
| 40902 | toast `message` | 重新拉取当前资源，刷新按钮可用状态 |
| 40903 | toast「请勿重复提交」 | 解除按钮 loading |
| 50000 | toast「服务暂不可用，请稍后重试」 | 保留用户输入，允许重试 |

**通用**：任何请求失败都要解除按钮 loading，否则用户会卡死在禁用状态。

---

## 11. 后端响应封装约定

- 统一用 `success(data)` 返回，`error_response` 由异常处理器产出，业务代码只 `raise BizException(code, message)`。
- 新增错误码必须先更新 §1.3 和 `ErrorCode` 枚举，再写代码。
- `message` 面向用户，可含具体业务信息（如「库存不足：TS-RED-L」），但**不得含堆栈、SQL、文件路径**。
- 分页一律走 `PageData.build(items, total, page, size)`，不要手拼。

---

## 12. 实现与文档差异（实测）

> 这一节是给「文档说的和代码做的不一样」留的账。**每一条都要有人拍板**：改代码，还是改文档。

| # | 项 | 文档口径 | 实际实现 | 建议 |
|---|---|---|---|---|
| D-01 | 加购不存在的 SKU | 404 | **40902**「商品规格不存在或已下架」 | 代码更合理（不暴露 id 是否存在），改文档 |
| D-02 | 列表是否过滤无库存商品 | 应隐藏 | **不过滤**，只给 `has_stock=false` | 产品确认（PRD Q1），建议保留并置「缺货」 |
| D-03 | 购物车角标口径 | 全部件数 | **只算有效项** | 代码更合理（与可结算数一致），改文档 |
| D-04 | 空 `cart_item_ids` 结算 | 400 | **200 + 空预览** | 前端拦截，后端保持 |
| D-05 | 管理端订单列表字段 | 含收货人/电话 | **不含**（`AdminOrderListItem` 未启用） | 运营需要就补，不需要就删掉死代码 |
| D-06 | 管理端 `status` 非法值 | 40001 | **不校验**，返回空列表 | 建议补校验，否则前端拿不到错误反馈 |
| D-07 | 停用账号登录 | 40100 | **40300**「账号已被停用」 | 403 语义更准，改文档 |
| D-08 | 创建商品/分类的响应 | 完整对象 | **ORM 裸对象**，无 `skus`/`children`，时间无时区 | 补响应模型，或明确「创建后重查」 |
| D-09 | 分类同级重名 | 40900 | **不校验**，允许重名 | 产品确认（PRD Q4） |
| D-10 | 时间输出时区 | 统一带偏移 | 仅 `UserOut` 带 `+00:00`，其余不带 | 统一 serializer，前端按 UTC 解析 |
| D-11 | 下单响应金额格式 | 两位小数字符串 | `str(Decimal)`，可能是 `"129.9"` | 改用 `format_price()` |
| D-12 | 分页超界 `size=101` | 40002 | **40001**（Pydantic 拦截） | 改文档为 40001 |
| D-13 | 地址接口响应字段 | 仅 `AddressOut` 8 个字段 | **多返回 `user_id`/`created_at`/`updated_at`** | 补 `response_model`，避免内部字段外泄 |

---

## 13. 已知缺陷与风险

| # | 问题 | 影响 | 建议 |
|---|---|---|---|
| B-01 | **编辑商品会重建全部 SKU，历史订单明细的 `sku_id` 被置 NULL**；而「删除商品」的订单关联检查正是靠 `order_items.sku_id` 关联 SKU | 有历史订单的商品在编辑一次后**可被删除**，删除保护失效，订单溯源断链 | 删除检查改用 `order_items.product_id`；编辑改为增量更新 SKU 而非全删重建 |
| B-02 | 定时任务开关 `ORDER_EXPIRE_JOB_ENABLED` **默认关闭** | 生产忘开则「30 分钟自动取消」不生效，库存可被恶意下单锁死 | 生产环境默认开启，启动日志打印任务状态 |
| B-03 | 登录失败计数存在进程内字典 | 多 worker / 重启后失效，防爆破形同虚设 | 迁 Redis（已在 PRD 已知限制中登记） |
| B-04 | 列表 `total` 用「查出全部再 len」实现 | 数据量上来后内存与耗时双高，P95 难达标 | 改 `SELECT COUNT(*)` |
| B-05 | 上传先整体读入内存再判大小 | 大文件会先占内存 | 边读边计数，超限即中断 |

**B-01 复现路径（3 步）**：新建商品并下单 → `PUT /admin/products/{id}`（任意修改）→ `DELETE /admin/products/{id}`。预期 40902，实际 200。

---

## 14. 变更流程

1. 改字段、改错误码、加接口 → 先改本文档，再改代码，PR 里两份一起提交。
2. 只改实现不改契约（重构、加索引）→ 不用动本文档。
3. 发现文档与代码不一致 → 记到 §12，不要在代码里「顺手对齐」而不留记录。
4. 本文档每次发版在表头更新版本号，并在 PR 描述里写清改了哪几条。
