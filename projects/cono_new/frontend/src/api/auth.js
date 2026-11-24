import request from './request'

export function login(data) {
  return request.post('/auth/login/', data)
}

export function getMenus() {
  return request.get('/auth/menus/')
}
