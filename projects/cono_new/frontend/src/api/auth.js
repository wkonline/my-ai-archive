import request from './request'

export function login(data) {
  return request.post('/auth/login/', data)
}

export function register(data) {
  return request.post('/auth/register/', data)
}

export function getRegisterDepartments() {
  return request.get('/auth/departments/')
}

export function getMenus() {
  return request.get('/auth/menus/')
}
