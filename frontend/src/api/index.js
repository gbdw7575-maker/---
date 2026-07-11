import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// ── User ──
export const userApi = {
  getDefault: () => api.get('/users/default'),
  get: (id) => api.get(`/users/${id}`),
  update: (id, data) => api.put(`/users/${id}`, data),
  create: (data) => api.post('/users', data),
}

// ── Health Indicators ──
export const healthApi = {
  list: (params) => api.get('/health/indicators', { params }),
  create: (data) => api.post('/health/indicators', data),
  batchCreate: (data) => api.post('/health/indicators/batch', data),
  get: (id) => api.get(`/health/indicators/${id}`),
  update: (id, data) => api.put(`/health/indicators/${id}`, data),
  delete: (id) => api.delete(`/health/indicators/${id}`),
  categories: () => api.get('/health/categories'),
  riskSummary: (params) => api.get('/health/risk-summary', { params }),
  suggestions: (params) => api.get('/health/suggestions', { params }),
  aiAnalyze: (params) => api.post('/health/ai-analyze', null, { params }),
}

// ── Chat ──
export const chatApi = {
  listSessions: (params) => api.get('/chat/sessions', { params }),
  createSession: (data) => api.post('/chat/sessions', data),
  getSession: (id) => api.get(`/chat/sessions/${id}`),
  deleteSession: (id) => api.delete(`/chat/sessions/${id}`),
  listMessages: (sessionId) => api.get(`/chat/sessions/${sessionId}/messages`),
  send: (data) => api.post('/chat/send', data),
}

// ── OCR ──
export const ocrApi = {
  recognize: (data, params) => api.post('/ocr/recognize', data, { params }),
}

// ── Medical Image Classification ──
export const classifyApi = {
  classifySkin: (data, params) => api.post('/classify/skin', data, { params }),
  classes: () => api.get('/classify/classes'),
  status: () => api.get('/classify/status'),
}

export default api
