import request from '@/utils/request'

export function login(data) {
  return request({
    url: '/automation/login',
    method: 'post',
    data
  })
}

export function register(data) {
  return request({
    url: '/automation/register',
    method: 'post',
    data
  })
}

export function personalChange(data) {
  return request({
    url: '/automation/personal',
    method: 'post',
    data
  })
}

export function getInfo(data) {
  return request({
    url: '/automation/info',
    method: 'post',
    data
    // method: 'get',
    // params: {
    //   token
    // }
  })
}

export function logout() {
  return request({
    url: '/automation/logout',
    method: 'post'
  })
}


export function queryDevices(data) {
  return request({
    url: '/automation/query_device',
    method: 'post',
    data
  })
}

export function sendCommand(data) {
  return request({
    url: '/automation/command',
    method: 'post',
    data
  })
}

export function deviceHistory(data) {
  return request({
    url: '/automation/device_history',
    method: 'post',
    data
  })
}

export function deviceHistoryDetail(data) {
  return request({
    url: '/automation/history_detail',
    method: 'post',
    data
  })
}
