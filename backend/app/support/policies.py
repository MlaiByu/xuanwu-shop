"""政策知识库：客服回答的“事实来源”之一。

规模只有十几条，用关键词打分检索足够；条目变多（>200）再换 pgvector / 全文索引。
注意每条答案都必须写具体数字（时效、门槛），客服最忌讳“以实际为准”这种模糊话术。
"""

from typing import Any

POLICIES: list[dict[str, Any]] = [
    {
        "id": "return",
        "title": "7 天无理由退换",
        "keywords": ["退货", "换货", "无理由", "七天", "7天", "不想要", "退换", "退掉"],
        "answer": (
            "支持 7 天无理由退换：签收次日起算，商品不影响二次销售即可"
            "（吊牌/包装/配件齐全）。定制类、拆封的食品与个护不支持无理由。"
            "在「我的订单」里点「申请售后」提交，审核通过后按页面地址寄回。"
        ),
    },
    {
        "id": "refund_time",
        "title": "退款时效",
        "keywords": ["退款", "多久到账", "到账", "退回", "原路"],
        "answer": (
            "退款审核通过后原路退回：微信/支付宝 1-3 个工作日到账，"
            "银行卡 3-7 个工作日。订单取消的库存会立即释放，款项按同样规则退回。"
        ),
    },
    {
        "id": "shipping_fee",
        "title": "运费与包邮",
        "keywords": ["运费", "包邮", "邮费", "快递费", "顺丰", "多少钱运费"],
        "answer": "活动期间全场包邮，默认顺丰发出，不额外收运费。偏远地区（新疆、西藏等）会改发邮政，时效多 1-2 天。",
    },
    {
        "id": "delivery",
        "title": "发货时效",
        "keywords": ["发货", "什么时候发", "多久发", "48小时", "催发货", "备货"],
        "answer": "付款后 48 小时内发出，节假日顺延。发出后可在「我的订单」看到快递单号；超过 48 小时未发会补偿 10 元无门槛券。",
    },
    {
        "id": "invoice",
        "title": "发票",
        "keywords": ["发票", "开票", "报销", "税号", "专票"],
        "answer": "支持开电子普票：下单时在备注写「需要发票 + 抬头 + 税号」，或收货后在订单详情点「申请开票」，48 小时内发到你的邮箱。专票需联系人工。",
    },
    {
        "id": "payment",
        "title": "支付方式",
        "keywords": ["支付", "付款", "微信", "支付宝", "银行卡", "分期"],
        "answer": "支持微信支付和支付宝；单笔满 500 元可 3 期免息（以支付页面展示为准）。订单提交后 15 分钟内未支付会自动关闭，库存释放。",
    },
    {
        "id": "address_change",
        "title": "修改收货地址",
        "keywords": ["改地址", "修改地址", "地址写错", "换地址", "地址填错"],
        "answer": "未发货可以直接改：订单详情 →「修改地址」。已发货就改不了，需要联系快递改派，或拒收后重新下单。",
    },
    {
        "id": "cancel",
        "title": "取消订单",
        "keywords": ["取消订单", "不买了", "关闭订单", "取消掉"],
        "answer": "待支付订单可以直接取消，库存立即释放；已支付但未发货的，申请退款后我们拦截发货；已发货的按退货流程处理。",
    },
    {
        "id": "stock",
        "title": "缺货与补货",
        "keywords": ["缺货", "补货", "没货", "什么时候有货", "断货"],
        "answer": "缺货商品通常 7-15 天补货。商品页点「到货提醒」，补货后第一时间短信通知；急用可以看看同价位的替代款。",
    },
    {
        "id": "quality",
        "title": "质量问题与保修",
        "keywords": ["质量", "坏了", "故障", "保修", "维修", "破损"],
        "answer": "非人为质量问题 15 天内可换新、1 年内保修（数码类按品牌政策）。收到破损请 48 小时内拍照上传，运费我们承担。",
    },
]


def _score(query: str, item: dict[str, Any]) -> int:
    """关键词命中打分。

    - 命中一个关键词 +3（强信号）
    - 标题字符重合按**去重后**的字符数 +1（弱信号，只用来打破平局）

    去重很关键：否则「缺货与补货」里两个「货」字会让「怎么申请退货」误命中。
    """
    score = 0
    for word in item["keywords"]:
        if word in query:
            score += 3
    score += len(set(item["title"]) & set(query))
    return score


def search_policies(query: str, limit: int = 2) -> list[dict[str, Any]]:
    """返回命中的政策条目（按相关度倒序）。

    阈值 3 表示至少要命中一个关键词；纯字符重合（最多 2 个）不足以判定命中。
    """
    if not query:
        return []
    scored = [(item, _score(query, item)) for item in POLICIES]
    hits = [(item, s) for item, s in scored if s >= 3]
    hits.sort(key=lambda pair: pair[1], reverse=True)
    return [item for item, _ in hits[:limit]]


def policy_titles() -> list[str]:
    return [item["title"] for item in POLICIES]
