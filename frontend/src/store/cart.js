import { defineStore } from 'pinia'
import { getCart, addCart, updateCart, removeCart } from '@/api'
import { useUserStore } from './user'

const GUEST_KEY = 'xw_guest_cart'

/**
 * 门店购物车：游客可加购（本地持久化），登录后自动并入服务端购物车。
 *
 * 两种数据源统一成同一个视图模型：
 * { key, id, server, skuId, productId, name, image, attrs, priceCents, qty, stock, valid }
 * 金额一律用「分」做整数计算，避免浮点误差。
 */

function readGuest() {
  try {
    const raw = JSON.parse(localStorage.getItem(GUEST_KEY) || '[]')
    return Array.isArray(raw) ? raw : []
  } catch (e) {
    return []
  }
}

function writeGuest(items) {
  localStorage.setItem(GUEST_KEY, JSON.stringify(items))
}

function centsOf(value) {
  return Math.round(Number(value || 0) * 100)
}

// 库存上限：`stock || 999` 会把 0 当成 999（0 是 falsy），导致无库存商品能加到上限。
// 这里显式区分「没有库存信息」与「库存为 0」。
function stockCap(stock) {
  const n = Number(stock)
  return Number.isFinite(n) && n >= 0 ? n : 999
}

// 数量夹取：结果始终落在 [1, 999]，同时受库存上限约束。
// 库存为 0 时 hi 取 1，保证不破坏「数量 ≥ 1」的不变量（失效态由 valid 标志表达）。
function qtyClamp(qty, stock) {
  const hi = Math.max(1, Math.min(stockCap(stock), 999))
  return Math.min(Math.max(1, Math.round(qty)), hi)
}

function fromServerItem(item) {
  return {
    key: `s${item.id}`,
    id: item.id,
    server: true,
    skuId: item.sku_id,
    productId: item.product_id,
    name: item.product_name,
    image: item.main_image,
    attrs: item.attrs || {},
    priceCents: centsOf(item.price),
    qty: item.quantity,
    stock: item.stock,
    valid: item.is_valid
  }
}

function fromGuestItem(item) {
  return {
    key: `g${item.skuId}`,
    id: `g${item.skuId}`,
    server: false,
    skuId: item.skuId,
    productId: item.productId,
    name: item.name,
    image: item.image,
    attrs: item.attrs || {},
    priceCents: item.priceCents,
    qty: item.qty,
    stock: item.stock,
    valid: item.valid !== false && item.stock > 0
  }
}

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [],
    checked: [],
    loaded: false,
    busy: false
  }),

  getters: {
    validItems: (s) => s.items.filter((i) => i.valid),
    invalidItems: (s) => s.items.filter((i) => !i.valid),
    count: (s) => s.items.reduce((sum, i) => (i.valid ? sum + i.qty : sum), 0),
    checkedItems: (s) => s.items.filter((i) => i.valid && s.checked.includes(i.key)),
    checkedCount() {
      return this.checkedItems.reduce((sum, i) => sum + i.qty, 0)
    },
    subtotalCents() {
      return this.checkedItems.reduce((sum, i) => sum + i.priceCents * i.qty, 0)
    },
    /**
     * 运费：后端 /orders/checkout 固定返回 "0.00"（活动期全场包邮），
     * 这里保持与结算页一致，避免购物车算出的金额和订单金额对不上。
     */
    shippingCents() {
      return 0
    },
    payableCents() {
      return this.subtotalCents
    },
    allChecked: (s) => {
      const valid = s.items.filter((i) => i.valid)
      return valid.length > 0 && valid.every((i) => s.checked.includes(i.key))
    }
  },

  actions: {
    async load() {
      // 并发闸：角标、购物车页、结算页可能同时触发 load()，复用同一个在途请求，
      // 避免后返回的旧快照覆盖新结果（审查报告 m10）。
      if (this._loadPromise) return this._loadPromise
      this._loadPromise = this._doLoad()
      try {
        return await this._loadPromise
      } finally {
        this._loadPromise = null
      }
    },

    async _doLoad() {
      const userStore = useUserStore()
      if (userStore.isLoggedIn) {
        await this.mergeGuest()
        try {
          const data = await getCart(true)
          this.items = (data.items || []).map(fromServerItem)
        } catch (e) {
          // 静默失败：角标不打扰用户，保持上一次结果
        }
      } else {
        this.items = readGuest().map(fromGuestItem)
      }
      this.syncChecked()
      this.loaded = true
    },

    async mergeGuest() {
      const guest = readGuest()
      if (!guest.length) return
      for (const item of guest) {
        try {
          await addCart({ sku_id: item.skuId, quantity: item.qty })
        } catch (e) {
          // 已下架 / 库存不足的条目直接丢弃，不阻断登录后的合并
        }
      }
      writeGuest([])
    },

    async add(product, sku, qty = 1) {
      const userStore = useUserStore()
      if (userStore.isLoggedIn) {
        await addCart({ sku_id: sku.id, quantity: qty })
        await this.load()
        // 新加入的条目默认勾选：load() 之后 checked 只保留原有选项，
        // 不补这一行的话刚加购的商品是未勾选状态，用户会以为没加进去。
        const added = this.items.find((i) => i.skuId === sku.id)
        if (added) this.checked = Array.from(new Set([...this.checked, added.key]))
        return
      }
      const guest = readGuest()
      const exist = guest.find((i) => i.skuId === sku.id)
      if (exist) {
        exist.qty = qtyClamp(exist.qty + qty, sku.stock)
      } else {
        guest.push({
          skuId: sku.id,
          productId: product.id,
          name: product.name,
          image: product.main_image,
          attrs: sku.attrs || {},
          priceCents: centsOf(sku.price),
          qty: qtyClamp(qty, sku.stock),
          stock: sku.stock,
          valid: sku.is_active !== false && sku.stock > 0
        })
      }
      writeGuest(guest)
      this.items = guest.map(fromGuestItem)
      this.checked = Array.from(new Set([...this.checked, `g${sku.id}`]))
    },

    async setQty(item, qty) {
      const next = qtyClamp(qty, item.stock)
      if (next === item.qty) return
      const target = this.items.find((i) => i.key === item.key)
      if (!target) return
      const prev = target.qty
      target.qty = next
      if (target.server) {
        try {
          await updateCart(target.id, { quantity: next })
        } catch (e) {
          target.qty = prev
        }
      } else {
        const guest = readGuest().map((i) =>
          i.skuId === target.skuId ? { ...i, qty: next } : i
        )
        writeGuest(guest)
      }
    },

    async remove(item) {
      if (item.server) {
        await removeCart(item.id)
        this.items = this.items.filter((i) => i.key !== item.key)
      } else {
        writeGuest(readGuest().filter((i) => i.skuId !== item.skuId))
        this.items = this.items.filter((i) => i.key !== item.key)
      }
      this.checked = this.checked.filter((k) => k !== item.key)
    },

    toggle(key) {
      this.checked = this.checked.includes(key)
        ? this.checked.filter((k) => k !== key)
        : [...this.checked, key]
    },

    toggleAll(value) {
      this.checked = value ? this.validItems.map((i) => i.key) : []
    },

    syncChecked() {
      const validKeys = new Set(this.validItems.map((i) => i.key))
      // 首次载入才默认全选；之后的载入要尊重用户「主动全不选」的结果。
      // 原先用 `kept.length ? kept : 全选` 判断，checked 为空数组时无法区分
      // 「还没初始化」和「用户取消了全部勾选」，导致一刷新又全选回来（审查报告 M6）。
      if (!this.loaded) {
        this.checked = Array.from(validKeys)
        return
      }
      this.checked = this.checked.filter((k) => validKeys.has(k))
    }
  }
})
