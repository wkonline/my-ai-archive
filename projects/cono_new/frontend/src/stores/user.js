import { defineStore } from 'pinia'
import { login as apiLogin } from '../api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('access_token') || '',
    user: JSON.parse(localStorage.getItem('user_info') || 'null'),
    permissions: JSON.parse(localStorage.getItem('user_permissions') || '[]'),
    menus: JSON.parse(localStorage.getItem('user_menus') || '[]'),
  }),
  getters: {
    isAdmin: (state) => (state.user?.role || '') === 'admin',
    hasPerm: (state) => (code) => {
      if ((state.user?.role || '') === 'admin') return true
      return (state.permissions || []).includes(code)
    },
  },
  actions: {
    async login(payload) {
      const data = await apiLogin(payload)
      this.token = data.access
      this.user = data.user
      this.permissions = data.user?.permissions || []
      this.menus = data.user?.menus || []
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      localStorage.setItem('user_info', JSON.stringify(data.user))
      localStorage.setItem('user_permissions', JSON.stringify(this.permissions))
      localStorage.setItem('user_menus', JSON.stringify(this.menus))
      return data
    },
    logout() {
      this.token = ''
      this.user = null
      this.permissions = []
      this.menus = []
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')
      localStorage.removeItem('user_permissions')
      localStorage.removeItem('user_menus')
    },
  },
})
