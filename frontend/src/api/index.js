import request from './request'

export const register = (data) => request.post('/auth/register', data)
export const login = (account, password) => request.post('/auth/login', { account, password })
export const logout = () => request.post('/auth/logout')
export const getMe = () => request.get('/auth/me')

export const getCategories = () => request.get('/categories')
export const getProducts = (params) => request.get('/products', { params })
export const getProductDetail = (id) => request.get(`/products/${id}`)

export const getCart = (silent = false) => request.get('/cart', { silent })
export const addCart = (data) => request.post('/cart', data)
export const updateCart = (id, data) => request.patch(`/cart/${id}`, data)
export const removeCart = (id) => request.delete(`/cart/${id}`)

export const getAddresses = () => request.get('/addresses')
export const createAddress = (data) => request.post('/addresses', data)
export const updateAddress = (id, data) => request.put(`/addresses/${id}`, data)
export const removeAddress = (id) => request.delete(`/addresses/${id}`)
export const setDefaultAddress = (id) => request.patch(`/addresses/${id}/default`)

export const getCheckout = (cart_item_ids) => request.get('/orders/checkout', { params: { cart_item_ids } })
export const createOrder = (data, idempotencyKey) =>
  request.post('/orders', data, { headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {} })
export const getOrders = (params) => request.get('/orders', { params })
export const getOrderDetail = (id) => request.get(`/orders/${id}`)
export const payOrder = (id) => request.post(`/orders/${id}/pay`)
export const cancelOrder = (id) => request.post(`/orders/${id}/cancel`)
export const confirmOrder = (id) => request.post(`/orders/${id}/confirm`)

export const adminGetProducts = (params) => request.get('/admin/products', { params })
export const adminGetProduct = (id) => request.get(`/admin/products/${id}`)
export const adminCreateProduct = (data) => request.post('/admin/products', data)
export const adminUpdateProduct = (id, data) => request.put(`/admin/products/${id}`, data)
export const adminDeleteProduct = (id) => request.delete(`/admin/products/${id}`)
export const adminSetProductStatus = (id, is_active) => request.patch(`/admin/products/${id}/status`, { is_active })

export const adminCreateCategory = (data) => request.post('/admin/categories', data)
export const adminUpdateCategory = (id, data) => request.put(`/admin/categories/${id}`, data)
export const adminDeleteCategory = (id) => request.delete(`/admin/categories/${id}`)

export const adminGetOrders = (params) => request.get('/admin/orders', { params })
export const adminShipOrder = (id) => request.post(`/admin/orders/${id}/ship`)

export const uploadImage = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request.post('/admin/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
}

// 商家端（B 端）
export const applyMerchant = (data) => request.post('/merchant/apply', data)
export const getMerchantProfile = () => request.get('/merchant/profile')
export const getMerchantProducts = () => request.get('/merchant/products')
export const createMerchantProduct = (data) => request.post('/merchant/products', data)
export const updateMerchantProduct = (id, data) => request.put(`/merchant/products/${id}`, data)
export const deleteMerchantProduct = (id) => request.delete(`/merchant/products/${id}`)
export const setMerchantProductStatus = (id, is_active) => request.patch(`/merchant/products/${id}/status`, { is_active })
export const getMerchantOrders = (params) => request.get('/merchant/orders', { params })

// 商家审核（超管）
export const getMerchants = (params) => request.get('/admin/merchants', { params })
export const approveMerchant = (id) => request.post(`/admin/merchants/${id}/approve`)
export const rejectMerchant = (id, remark) => request.post(`/admin/merchants/${id}/reject`, { remark })

// 管理员管理（超管）
export const getAdmins = () => request.get('/admin/admins')
export const createAdmin = (data) => request.post('/admin/admins', data)
export const deleteAdmin = (id) => request.delete(`/admin/admins/${id}`)
export const setAdminStatus = (id, is_active) => request.patch(`/admin/admins/${id}/status`, { is_active })
