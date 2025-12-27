import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

window.ipcRenderer = ipcRenderer

const api = {
  login: (data) => ipcRenderer.invoke('login', data),
  register: (data) => ipcRenderer.invoke('register', data),
  logout: () => ipcRenderer.invoke('logout'),
  checkAutoLogin: () => ipcRenderer.invoke('check-auto-login'),
  bindThirdParty: (brandName, authCode) => ipcRenderer.invoke('bind-third-party', brandName, authCode),
  unbindThirdParty: (brandName) => ipcRenderer.invoke('unbind-third-party', brandName),
  getBindings: () => ipcRenderer.invoke('get-bindings'),
  getAuthorizationCode: (userId) => ipcRenderer.invoke('get-authorization-code', userId),
  refreshToken: () => ipcRenderer.invoke('refresh-token'),
  // 存储管理
  forceCleanupStorage: () => ipcRenderer.invoke('force-cleanup-storage'),
  getStorageStatus: () => ipcRenderer.invoke('get-storage-status')
}

// 创建完整的 electronAPI 对象，包含 invoke 方法
const customElectronAPI = {
  ...electronAPI,
  invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args)
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', customElectronAPI)
    contextBridge.exposeInMainWorld('electronAPI', customElectronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  window.electron = customElectronAPI
  window.electronAPI = customElectronAPI
  window.api = api
}
