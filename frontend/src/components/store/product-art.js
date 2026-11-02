/**
 * 商品占位铜版：类目线描 + 纸感底色。
 *
 * 背景：后端演示数据里的商品图是随机占位图（picsum），与商品语义无关，
 * 直接展示反而伤害信任；上传的真实商品图（/static/**）仍会正常显示。
 * 这里用一套统一的线描 + 色板兜底，保证列表在无图 / 图裂时仍然是"设计过的"。
 *
 * 安全约束：artFor() 只返回下方 ART 这个封闭映射里的静态 SVG 字符串，不含任何插值。
 * Home.vue / ProductMedia.vue 用 v-html 渲染它的返回值——这是安全的，前提是
 * 以后任何人往 ART 里加图或改 artFor 时，都不允许拼入用户输入 / 接口字段。
 */

const ART = {
  phone:
    '<rect x="22" y="9" width="20" height="46" rx="4"/><path d="M28.5 15h7"/><circle cx="32" cy="49" r="1.6"/>',
  audio:
    '<path d="M16 36v-5a16 16 0 0 1 32 0v5"/><rect x="12" y="35" width="8" height="15" rx="3"/><rect x="44" y="35" width="8" height="15" rx="3"/>',
  computer:
    '<rect x="14" y="16" width="36" height="24" rx="2"/><path d="M10 46h44l-3 6H13z"/><path d="M29 40h6"/>',
  peripheral:
    '<rect x="10" y="22" width="44" height="20" rx="2"/><path d="M18 30h2M26 30h2M34 30h2M42 30h2M18 38h28"/>',
  fridge:
    '<rect x="18" y="8" width="28" height="48" rx="3"/><path d="M18 26h28M24 16v6M24 32v8"/>',
  washer:
    '<rect x="14" y="8" width="36" height="48" rx="3"/><circle cx="32" cy="37" r="11"/><circle cx="32" cy="37" r="4.5"/><path d="M20 16h6M44 16h2"/>',
  apparel:
    '<path d="M24 12l8 4 8-4 9 7-6 7v26H21V26l-6-7z"/><path d="M28 20c1.4 2.6 6.6 2.6 8 0"/>',
  shoe:
    '<path d="M10 40h14l5-8 5 3h10l6 5h4v8H13a3 3 0 0 1-3-3z"/><path d="M29 35l4 5M35 38l3 3"/>',
  beauty:
    '<rect x="27" y="8" width="10" height="7" rx="1"/><path d="M24 15h16v34a7 7 0 0 1-7 7h-2a7 7 0 0 1-7-7z"/><path d="M24 30h16"/>',
  bottle:
    '<path d="M26 8h12v6l4 6v30a6 6 0 0 1-6 6h-8a6 6 0 0 1-6-6V20l4-6z"/><path d="M23 30h18"/>',
  snack:
    '<path d="M20 14h24l3 36a5 5 0 0 1-5 5H22a5 5 0 0 1-5-5z"/><path d="M18 14l4-6h20l4 6M25 26h14M25 34h10"/>',
  drink:
    '<path d="M20 12h24l-3 40a6 6 0 0 1-6 5h-6a6 6 0 0 1-6-5z"/><path d="M18 22h28M26 6h12"/>',
  bed:
    '<path d="M12 46V30h28v16M12 38h40v8M40 30h12v16M16 30v-6h10v6"/>',
  box:
    '<path d="M12 18l20-8 20 8v28l-20 8-20-8z"/><path d="M12 18l20 8 20-8M32 26v28"/>',
  dumbbell:
    '<path d="M12 32h40"/><rect x="9" y="24" width="6" height="16" rx="1"/><rect x="49" y="24" width="6" height="16" rx="1"/><rect x="18" y="28" width="4" height="8"/><rect x="42" y="28" width="4" height="8"/>',
  tent:
    '<path d="M32 10L54 52H10z"/><path d="M32 10v42M22 52l10-18 10 18"/>',
  chair:
    '<path d="M20 12v24h24V12"/><path d="M20 24h24"/><path d="M14 44h36"/><path d="M18 36v8M46 36v8"/>',
  lamp:
    '<path d="M22 38h20l-5-20H27z"/><path d="M32 38v10"/><path d="M24 52h16"/>',
  pot:
    '<path d="M16 26h32l-3 18a5 5 0 0 1-5 4H24a5 5 0 0 1-5-4z"/><path d="M16 26l-3-6M48 26l3-6"/><path d="M22 26V18h20v8"/>'
}

const RULES = [
  [/折叠椅|椅子|凳子|沙发/, 'chair'],
  [/台灯|落地灯|灯具|照明/, 'lamp'],
  [/锅|炉|水壶|保温杯/, 'pot'],
  [/手机|通讯/, 'phone'],
  [/耳机|音频|音箱/, 'audio'],
  [/笔记本|电脑|平板/, 'computer'],
  [/外设|键盘|鼠标|配件/, 'peripheral'],
  [/冰箱/, 'fridge'],
  [/洗衣|空调|家电/, 'washer'],
  [/男装|女装|服饰|外套|衣/, 'apparel'],
  [/鞋|靴/, 'shoe'],
  [/护肤|美妆|香氛/, 'beauty'],
  [/洗护|清洁/, 'bottle'],
  [/零食|生鲜|食品/, 'snack'],
  [/饮料|冲调|咖啡|茶/, 'drink'],
  [/床品|家纺|沙发|家具/, 'bed'],
  [/收纳|整理/, 'box'],
  [/健身|运动器械/, 'dumbbell'],
  [/露营|户外|帐篷/, 'tent']
]

const TINTS = [
  '#e9e0cf',
  '#e7d5c9',
  '#dde0d2',
  '#dce0e3',
  '#eee3cb',
  '#e6d9d6',
  '#dfe2d6'
]

function hash(input) {
  let h = 0
  for (let i = 0; i < input.length; i += 1) {
    h = (h * 31 + input.charCodeAt(i)) >>> 0
  }
  return h
}

export function artFor(...hints) {
  const text = hints.filter(Boolean).join(' ')
  const hit = RULES.find(([re]) => re.test(text))
  return ART[hit ? hit[1] : 'box']
}

export function tintFor(seed) {
  return TINTS[hash(String(seed || 'xuanwu')) % TINTS.length]
}
