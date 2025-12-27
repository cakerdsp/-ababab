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
  refreshToken: () => ipcRenderer.invoke('refresh-token')
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  window.electron = electronAPI
  window.api = api
}
