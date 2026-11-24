/**
 * 字典缓存 Store
 * 缓存在线基础数据（产品分类、产品型号、合同等），避免频繁请求
 * 
 * 使用方式：
 * import { useDictStore } from '@/stores/dictCache'
 * const dict = useDictStore()
 * await dict.fetchAll() // 首次或过期时刷新
 * const categories = dict.categories // 直接使用
 */
import { defineStore } from 'pinia'
import request from '../api/request'

export const useDictStore = defineStore('dict', {
  state: () => ({
    // 各类字典数据
    categories: [],
    products: [],
    contracts: [],
    // 过期时间戳 (毫秒)
    _expireAt: 0,
    // 过期间隔，单位毫秒（默认 60 秒）
    TTL: 60 * 1000,
  }),
  
  getters: {
    isExpired: (state) => Date.now() > state._expireAt,
    categoryMap: (state) => new Map(state.categories.map(c => [c.id, c])),
    productMap: (state) => new Map(state.products.map(p => [p.id, p])),
    contractMap: (state) => new Map(state.contracts.map(c => [c.id, c])),
  },
  
  actions: {
    async fetchCategories() {
      const res = await request.get('/productcategory/?page_size=200', { silent: true })
      this.categories = res.results || []
    },
    
    async fetchProducts() {
      const res = await request.get('/product/?page_size=200', { silent: true })
      this.products = res.results || []
    },
    
    async fetchContracts() {
      const res = await request.get('/contract/?page_size=200', { silent: true })
      this.contracts = res.results || []
    },
    
    /** 批量获取所有字典数据（过期时才重新请求） */
    async fetchAll() {
      if (!this.isExpired && this.categories.length > 0) return
      
      await Promise.all([
        this.fetchCategories(),
        this.fetchProducts(),
        this.fetchContracts(),
      ])
      
      // 更新过期时间
      this._expireAt = Date.now() + this.TTL
    },
    
    /** 清除缓存（可在用户修改了基础数据后调用） */
    clear() {
      this.categories = []
      this.products = []
      this.contracts = []
      this._expireAt = 0
    },
  },
})
