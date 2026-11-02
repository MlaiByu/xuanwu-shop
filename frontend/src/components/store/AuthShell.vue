<template>
  <div class="auth">
    <section class="auth-main">
      <RouterLink to="/" class="auth-brand" aria-label="回到首页">
        <span class="xw-brand-cn">玄武</span>
        <span class="xw-brand-en">XUANWU</span>
      </RouterLink>

      <div class="auth-body">
        <slot />
      </div>

      <p class="auth-foot">
        © 2026 玄武商城 · 满 ¥199 顺丰包邮 · 7 天无理由退换
      </p>
    </section>

    <aside class="auth-aside" aria-hidden="true">
      <div class="auth-aside-inner">
        <span class="auth-aside-eyebrow">XUANWU · 生活选物</span>
        <h2>值得买的，<br />其实不多。</h2>

        <ul class="auth-points">
          <li v-for="item in points" :key="item.no">
            <span class="no">{{ item.no }}</span>
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.desc }}</p>
            </div>
          </li>
        </ul>
      </div>
    </aside>
  </div>
</template>

<script setup>
const points = [
  { no: '01', title: '参数写清楚', desc: '规格、库存、发货时间都在商品页上' },
  { no: '02', title: '运费不藏', desc: '满 199 顺丰包邮，购物车里先算给你看' },
  { no: '03', title: '退货不绕弯', desc: '7 天无理由，原路退回，不追问理由' }
]
</script>

<style scoped>
.auth {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 0.82fr);
  background: var(--xw-paper);
  color: var(--xw-ink);
  font-family: var(--xw-font-sans);
}

.auth-main {
  display: flex;
  flex-direction: column;
  padding: 36px clamp(28px, 6vw, 88px) 28px;
}

.auth-brand {
  display: inline-flex;
  align-items: baseline;
  gap: 9px;
  align-self: flex-start;
}

.auth-brand .xw-brand-cn {
  font-size: 19px;
  font-weight: 600;
  letter-spacing: 0.22em;
}

.auth-brand .xw-brand-en {
  font-family: var(--xw-font-serif);
  font-size: 9.5px;
  letter-spacing: 0.34em;
  color: var(--xw-muted);
}

.auth-body {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 40px 0;
  animation: auth-rise 0.5s var(--xw-ease) both;
}

.auth-body > :deep(*) {
  width: 100%;
  max-width: 392px;
}

.auth-foot {
  font-size: 10.5px;
  letter-spacing: 0.04em;
  color: var(--xw-muted);
}

/* ---------- 右侧品牌栏 ---------- */
.auth-aside {
  position: relative;
  overflow: hidden;
  background: var(--xw-ink);
  color: #ece2d0;
}

.auth-aside-inner {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 64px clamp(36px, 4.4vw, 72px);
  animation: auth-rise 0.6s var(--xw-ease) 0.08s both;
}

@keyframes auth-rise {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.auth-aside-eyebrow {
  font-size: 10px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: #a89a83;
}

.auth-aside h2 {
  margin: 22px 0 40px;
  font-size: clamp(28px, 2.6vw, 38px);
  line-height: 1.25;
  font-weight: 500;
  letter-spacing: -0.03em;
  color: #f6efe2;
}

.auth-points {
  display: grid;
  gap: 22px;
  max-width: 340px;
}

.auth-points li {
  display: flex;
  gap: 14px;
  padding-top: 22px;
  border-top: 1px solid rgba(236, 226, 208, 0.16);
}

.auth-points li:first-child {
  padding-top: 0;
  border-top: 0;
}

.auth-points .no {
  font-family: var(--xw-font-serif);
  font-size: 11px;
  letter-spacing: 0.12em;
  color: #a89a83;
  padding-top: 2px;
}

.auth-points strong {
  display: block;
  font-size: 12.5px;
  font-weight: 500;
  color: #f2ebde;
  letter-spacing: 0.01em;
}

.auth-points p {
  margin-top: 5px;
  font-size: 11.5px;
  line-height: 1.7;
  color: #a89a83;
}

@media (max-width: 900px) {
  .auth {
    grid-template-columns: 1fr;
  }
  .auth-aside {
    display: none;
  }
  .auth-main {
    padding: 22px var(--xw-gutter) 24px;
    min-height: 100vh;
  }
  .auth-body {
    align-items: flex-start;
    padding: 44px 0 32px;
  }
}
</style>
