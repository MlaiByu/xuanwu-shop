<template>
  <footer class="xw-footer">
    <div class="xw-shell">
      <div class="xw-footer-cols">
        <div class="xw-footer-brand">
          <span class="xw-brand">
            <span class="xw-brand-cn">玄武</span>
            <span class="xw-brand-en">XUANWU</span>
          </span>
          <p>
            一间把参数讲清楚、把价格标明白的选物店。24 个类目，每一件都想清楚
            为什么值得买，再放进货架。
          </p>
        </div>

        <div>
          <h4>选购</h4>
          <ul>
            <li><RouterLink to="/products">全部商品</RouterLink></li>
            <li><RouterLink to="/products?sort=sales_desc">销量榜</RouterLink></li>
            <li><RouterLink to="/cart">购物车</RouterLink></li>
            <li><RouterLink to="/orders">我的订单</RouterLink></li>
          </ul>
        </div>

        <div>
          <h4>配送与售后</h4>
          <ul>
            <li><span>满 199 元顺丰包邮</span></li>
            <li><span>48 小时内发出</span></li>
            <li><span>7 天无理由退换</span></li>
            <li><span>一年质保 · 全国联保</span></li>
          </ul>
        </div>

        <div>
          <h4>联系我们</h4>
          <ul>
            <li><span>客服 400-020-1799</span></li>
            <li><span>每日 9:00 - 22:00</span></li>
            <li><span>service@xuanwu.shop</span></li>
            <li><span>上海市徐汇区龙腾大道 2555 号</span></li>
          </ul>
        </div>
      </div>

      <div class="xw-footer-bottom">
        <span>© 2026 玄武商城 XUANWU · 演示项目，商品与价格仅作展示</span>
        <span class="xw-pay">
          <span>微信支付</span>
          <span>支付宝</span>
          <span>银联云闪付</span>
        </span>
      </div>
    </div>
  </footer>
</template>
