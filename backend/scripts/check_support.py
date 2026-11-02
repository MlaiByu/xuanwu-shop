"""客服模块冒烟自检（不连数据库、不调模型）。

    .venv/Scripts/python.exe -m scripts.check_support

覆盖三件最容易回归的事：意图分类、政策检索命中与误命中、订单号提取。
"""

from app.support.graph import _classify, _extract_product_keyword, _match_product_name
from app.support.policies import search_policies
from app.support.tools import extract_order_no

FAKE_NAMES = ["卫龙辣条", "卫龙魔芋爽", "iPhone 15 Pro", "小米 14", "AirPods Pro 2"]

NAME_CASES = [
    ("卫龙辣条", "卫龙辣条"),
    ("卫龙辣条还有多少", "卫龙辣条"),
    ("威龙辣条还有多少", "卫龙辣条"),
    ("有没有 iPhone", "iPhone 15 Pro"),
    ("你好", None),
]

INTENT_CASES = [
    ("我的订单到哪了", "order"),
    ("怎么申请退货", "policy"),
    ("能开发票吗", "policy"),
    ("有没有 iPhone", "product"),
    ("我要投诉，太坑了", "human"),
    ("你好", "chitchat"),
]

# (当前话, 上一轮意图, 期望意图) —— 多轮记忆回归
FOLLOWUP_CASES = [
    ("卫龙辣条", "product", "product"),
    ("多少钱", "product", "product"),
    ("有货吗", "product", "product"),
    ("那单什么时候到", "logistics", "logistics"),
    ("你好", "product", "chitchat"),
]

KEYWORD_CASES = [
    ("卫龙辣条", "卫龙辣条"),
    ("卫龙辣条有货吗", "卫龙辣条"),
    ("这个多少钱", ""),
]

POLICY_CASES = [
    ("怎么申请退货", "return"),
    ("多久能退款到账", "refund_time"),
    ("运费怎么算", "shipping_fee"),
    ("能开发票吗", "invoice"),
]

ORDER_NO = "20261031145727791888"


def main() -> int:
    failures = 0

    for text, expected in INTENT_CASES:
        actual, confidence = _classify(text)
        ok = actual == expected
        failures += 0 if ok else 1
        print(f"{'OK ' if ok else 'FAIL'} intent {text!r} -> {actual} ({confidence:.2f})，期望 {expected}")

    # 误命中回归：问退货不能带出「缺货与补货」（曾因标题字符重叠导致）
    hit_ids = [item["id"] for item in search_policies("怎么申请退货")]
    ok = "stock" not in hit_ids
    failures += 0 if ok else 1
    print(f"{'OK ' if ok else 'FAIL'} 退货查询不应命中 stock，实际 {hit_ids}")

    for text, prev, expected in FOLLOWUP_CASES:
        actual, _ = _classify(text, prev)
        ok = actual == expected
        failures += 0 if ok else 1
        print(f"{'OK ' if ok else 'FAIL'} followup {text!r}（上轮 {prev}）-> {actual}，期望 {expected}")

    for text, expected in KEYWORD_CASES:
        actual = _extract_product_keyword(text)
        ok = actual == expected
        failures += 0 if ok else 1
        print(f"{'OK ' if ok else 'FAIL'} keyword {text!r} -> {actual!r}，期望 {expected!r}")

    # 裸商品名 / 错别字要能对齐到标准商品名，否则会被判成闲聊
    for text, expected in NAME_CASES:
        actual = _match_product_name(text, FAKE_NAMES)
        ok = actual == expected
        failures += 0 if ok else 1
        print(f"{'OK ' if ok else 'FAIL'} 商品识别 {text!r} -> {actual!r}，期望 {expected!r}")

    for text, expected in POLICY_CASES:
        hits = search_policies(text)
        actual = hits[0]["id"] if hits else None
        ok = actual == expected
        failures += 0 if ok else 1
        print(f"{'OK ' if ok else 'FAIL'} policy {text!r} -> {actual}，期望 {expected}")

    found = extract_order_no(f"订单 {ORDER_NO} 到哪了")
    ok = found == ORDER_NO
    failures += 0 if ok else 1
    print(f"{'OK ' if ok else 'FAIL'} 订单号提取 -> {found}")

    print(f"\n{'全部通过' if failures == 0 else f'{failures} 项失败'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
