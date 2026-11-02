"""智能客服。

- `service.SupportService`：对外入口（会话 + 流式事件）
- `graph.build_graph()`：LangGraph 状态图
- `tools.*`：订单 / 物流 / 商品查询，全部带 user_id 作用域
- `policies.*`：退换货、运费、发票等政策知识（轻量检索，不依赖向量库）

说明：这里刻意不把 LangGraph 暴露给 API 层，方便后续换编排框架而不动路由。
"""
