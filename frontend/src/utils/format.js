export function formatPrice(value) {
  const n = Number(value || 0)
  return '¥' + n.toFixed(2)
}
