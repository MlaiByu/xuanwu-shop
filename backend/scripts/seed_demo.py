"""演示数据初始化脚本。

用法（backend 目录下）：
    .venv/Scripts/python.exe -m scripts.seed_demo            # 追加（已存在则跳过）
    .venv/Scripts/python.exe -m scripts.seed_demo --reset    # 清空业务表后重建

--reset 会删除商品/分类/订单/购物车相关数据，保留用户与地址。
"""
import sys

from sqlalchemy import delete, func, select, update

from app.database import SessionLocal
from app.models import (
    CartItem,
    Category,
    IdempotencyKey,
    Order,
    OrderItem,
    Product,
    Sku,
)
from app.services.product_service import build_attrs_key

# 商品数据：一级分类 -> 二级分类 -> 商品（name, desc, [(sku_code, attrs, price, stock, sales)])]
DEMO = [
    ("手机数码", [
        ("手机", [
            ("iPhone 15 Pro", "钛金属机身，A17 Pro 芯片", [
                ("IP15P-128-BLK", {"颜色": "黑色钛金属", "容量": "128G"}, "7999", 50, 320),
                ("IP15P-256-BLU", {"颜色": "蓝色钛金属", "容量": "256G"}, "8999", 30, 210),
            ]),
            ("小米 14", "骁龙8 Gen3，徕卡光学镜头", [
                ("MI14-12-BLK", {"颜色": "黑色", "容量": "12G+256G"}, "3999", 100, 860),
                ("MI14-12-WHT", {"颜色": "白色", "容量": "12G+512G"}, "4299", 60, 540),
                ("MI14-16-GRN", {"颜色": "绿色", "容量": "16G+1TB"}, "4999", 20, 130),
            ]),
            ("华为 Mate 60 Pro", "卫星通话，昆仑玻璃", [
                ("HW60-512-BLK", {"颜色": "雅丹黑", "容量": "512G"}, "6999", 40, 480),
                ("HW60-512-WHT", {"颜色": "白沙银", "容量": "512G"}, "6999", 35, 390),
            ]),
        ]),
        ("耳机音频", [
            ("AirPods Pro 2", "主动降噪，空间音频", [
                ("AP2-WHT", {"版本": "标准版"}, "1899", 200, 1500),
                ("AP2-WHT-USB", {"版本": "USB-C"}, "1899", 180, 900),
            ]),
            ("索尼 WH-1000XM5", "旗舰降噪头戴耳机", [
                ("XM5-BLK", {"颜色": "黑色"}, "2399", 90, 420),
                ("XM5-SLV", {"颜色": "银色"}, "2399", 70, 310),
            ]),
            ("小米蓝牙音箱", "便携防水，20 小时续航", [
                ("SPK-1", {"颜色": "灰色"}, "129", 500, 3200),
            ]),
        ]),
    ]),
    ("电脑办公", [
        ("笔记本电脑", [
            ("MacBook Air M3", "13.6 英寸，超长续航", [
                ("MBA-M3-8", {"配置": "8G+256G"}, "8999", 60, 280),
                ("MBA-M3-16", {"配置": "16G+512G"}, "10499", 40, 190),
            ]),
            ("联想小新 Pro 16", "高性能轻薄本", [
                ("LX-PRO-16", {"配置": "16G+1T"}, "5999", 80, 450),
            ]),
            ("华为 MateBook 14", "2.8K 触控屏", [
                ("MB14-GRY", {"颜色": "深空灰", "配置": "16G+512G"}, "5699", 70, 360),
            ]),
        ]),
        ("外设配件", [
            ("罗技 G502 鼠标", "游戏电竞鼠标", [
                ("G502", {"版本": "有线版"}, "399", 300, 2100),
            ]),
            ("雷蛇机械键盘", "RGB 光效，87 键", [
                ("RZ-KB", {"轴体": "红轴"}, "699", 150, 820),
                ("RZ-KB-BLU", {"轴体": "青轴"}, "699", 120, 610),
            ]),
        ]),
    ]),
    ("家用电器", [
        ("冰箱", [
            ("海尔对开门冰箱", "535 升，变频节能", [
                ("HR-535", {"颜色": "银色"}, "3299", 40, 210),
            ]),
            ("美的三门冰箱", "风冷无霜", [
                ("MD-3", {"颜色": "白色"}, "1899", 80, 460),
            ]),
        ]),
        ("洗衣机", [
            ("小天鹅滚筒洗衣机", "10KG 变频", [
                ("XTE-10", {"颜色": "白色"}, "2499", 60, 380),
            ]),
            ("海尔波轮洗衣机", "8KG 大容量", [
                ("HR-BL-8", {"颜色": "金色"}, "999", 120, 720),
            ]),
        ]),
    ]),
    ("服饰鞋包", [
        ("男装", [
            ("优衣库摇粒绒外套", "保暖轻便", [
                ("UQ-FLEECE-M", {"颜色": "深灰", "尺码": "M"}, "199", 200, 1500),
                ("UQ-FLEECE-L", {"颜色": "深灰", "尺码": "L"}, "199", 180, 1300),
            ]),
            ("李宁运动卫衣", "宽松休闲", [
                ("LN-HOODIE", {"颜色": "黑色", "尺码": "XL"}, "259", 150, 900),
            ]),
        ]),
        ("运动鞋", [
            ("耐克 Air Force 1", "经典百搭", [
                ("NK-AF1-40", {"尺码": "40"}, "799", 60, 1200),
                ("NK-AF1-42", {"尺码": "42"}, "799", 80, 1600),
                ("NK-AF1-44", {"尺码": "44"}, "799", 50, 800),
            ]),
            ("阿迪达斯 UltraBoost", "缓震跑鞋", [
                ("AD-UB-41", {"尺码": "41"}, "1099", 40, 520),
            ]),
        ]),
    ]),
    ("美妆个护", [
        ("护肤", [
            ("雅诗兰黛小棕瓶", "修护抗老精华", [
                ("EL-ANR-50", {"规格": "50ml"}, "880", 90, 1100),
            ]),
            ("兰蔻小黑瓶", "肌底精华液", [
                ("LAN-50", {"规格": "50ml"}, "860", 100, 1300),
            ]),
        ]),
        ("洗护", [
            ("清扬洗发水", "去屑控油", [
                ("QY-500", {"规格": "500ml"}, "49", 600, 8000),
            ]),
        ]),
    ]),
    ("食品生鲜", [
        ("休闲零食", [
            ("三只松鼠坚果礼盒", "每日坚果 30 包", [
                ("SZS-NUT", {"规格": "750g"}, "129", 300, 5000),
            ]),
            ("良品铺子肉脯", "靖江猪肉脯", [
                ("LP-ROU", {"规格": "300g"}, "59", 400, 4200),
            ]),
        ]),
        ("饮料冲调", [
            ("东方树叶乌龙茶", "0 糖 0 脂", [
                ("DFSY-15", {"规格": "15瓶装"}, "59", 500, 9000),
            ]),
            ("三顿半速溶咖啡", "冷萃冻干", [
                ("SDB-24", {"规格": "24颗"}, "129", 250, 3000),
            ]),
        ]),
    ]),
    ("家居家具", [
        ("床品家纺", [
            ("水星家纺四件套", "纯棉 A 类", [
                ("SX-4PCS", {"规格": "1.8m床"}, "399", 90, 640),
            ]),
            ("记忆棉枕头", "护颈助眠", [
                ("PLW-1", {"规格": "单只装"}, "129", 200, 2100),
            ]),
        ]),
        ("收纳整理", [
            ("可折叠收纳箱", "加厚大容量", [
                ("SNX-60", {"规格": "60L"}, "39", 800, 12000),
            ]),
        ]),
    ]),
    ("运动户外", [
        ("健身器械", [
            ("可调节哑铃", "快调 2-24KG", [
                ("DB-24", {"规格": "单只"}, "399", 70, 480),
            ]),
            ("瑜伽垫", "加厚防滑", [
                ("YG-10", {"规格": "10mm"}, "79", 400, 3500),
            ]),
        ]),
        ("露营装备", [
            ("迪卡侬帐篷", "三人速开", [
                ("DCN-TENT", {"规格": "3人"}, "499", 60, 320),
            ]),
            ("户外折叠椅", "轻量便携", [
                ("HD-YI", {"颜色": "军绿"}, "99", 200, 1800),
            ]),
        ]),
    ]),
]


def _reset(db) -> None:
    for model in (IdempotencyKey, OrderItem, Order, CartItem, Sku, Product):
        db.execute(delete(model))
    # 分类自引用：先断开父指针，否则 RESTRICT 阻止删除父分类
    db.execute(update(Category).values(parent_id=None))
    db.execute(delete(Category))
    db.commit()


def _seed(db) -> tuple[int, int, int]:
    cat_count = prod_count = sku_count = 0
    img_seq = 0
    for cat_name, sub_cats in DEMO:
        category = Category(name=cat_name, parent_id=None, level=1, sort=cat_count)
        db.add(category)
        db.flush()
        cat_count += 1

        for sub_name, products in sub_cats:
            sub = Category(name=sub_name, parent_id=category.id, level=2, sort=0)
            db.add(sub)
            db.flush()
            cat_count += 1

            for p_name, desc, skus in products:
                img_seq += 1
                product = Product(
                    name=p_name,
                    category_id=sub.id,
                    description=desc,
                    main_image=f"https://picsum.photos/seed/xuanwu{img_seq}/480/480",
                    images=[f"https://picsum.photos/seed/xuanwu{img_seq}a/480/480"],
                    is_active=True,
                    sales_count=max((s[4] for s in skus), default=0),
                )
                db.add(product)
                db.flush()
                prod_count += 1

                for code, attrs, price, stock, _sales in skus:
                    db.add(
                        Sku(
                            product_id=product.id,
                            sku_code=code,
                            attrs=attrs,
                            attrs_key=build_attrs_key(attrs),
                            price=price,
                            stock=stock,
                            is_active=True,
                        )
                    )
                    sku_count += 1
    db.commit()
    return cat_count, prod_count, sku_count


def main() -> int:
    reset = "--reset" in sys.argv
    db = SessionLocal()
    try:
        existing = db.scalar(select(func.count()).select_from(Category)) or 0
        if existing and not reset:
            print(f"已存在 {existing} 个分类，跳过。如需重建请加 --reset")
            return 0
        if reset:
            _reset(db)
            print("已清空商品/分类/订单/购物车数据")
        cats, prods, skus = _seed(db)
        print(f"完成：{cats} 个分类，{prods} 个商品，{skus} 个 SKU")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
