import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken')
      window.location.href = '/login'
    }

    const message = error.response?.data?.detail || error.response?.data?.message || error.message || 'An error occurred'

    if (error.response?.status >= 500) {
      toast.error('Server error: ' + message)
    } else if (error.response?.status >= 400) {
      toast.error(message)
    }

    return Promise.reject(error)
  }
)

export const apiClient = {
  // Boilerplate Manager
  getCategories: () => client.get('/boilerplate/categories'),

  getSections: (params) => client.get('/boilerplate/sections', { params }),

  createSection: (data) => client.post('/boilerplate/sections', data),

  updateSection: (id, data) => client.put(`/boilerplate/sections/${id}`, data),

  deleteSection: (id) => client.delete(`/boilerplate/sections/${id}`),

  searchBoilerplate: (query, params) => client.get(`/boilerplate/search?q=${query}`, { params }),

  getVersionHistory: (sectionId) => client.get(`/boilerplate/sections/${sectionId}/history`),

  // RFP Upload & Parse
  uploadRFP: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/rfp/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  listRFPs: (params) => client.get('/rfp/list', { params }),

  getRFP: (id) => client.get(`/rfp/${id}`),

  getRequirements: (rfpId) => client.get(`/rfp/${rfpId}/requirements`),

  deleteRFP: (id) => client.delete(`/rfp/${id}`),

  updateRFPParsing: (id, data) => client.put(`/rfp/${id}`, data),

  // Crosswalk Engine
  generateCrosswalk: (rfpId) => client.post('/crosswalk/generate', { rfp_id: rfpId }),

  getCrosswalk: (id) => client.get(`/crosswalk/${id}`),

  getMatrix: (rfpId) => client.get(`/crosswalk/matrix/${rfpId}`),

  updateMapping: (id, data) => client.put(`/crosswalk/mapping/${id}`, data),

  approveMapping: (id) => client.post(`/crosswalk/mapping/${id}/approve`),

  exportCrosswalk: (rfpId) => client.get(`/crosswalk/export/${rfpId}`, { responseType: 'blob' }),

  // Grant Plan Generator
  generatePlan: (data) => client.post('/plan/generate', data),

  listPlans: (params) => client.get('/plan/list', { params }),

  getPlan: (id) => client.get(`/plan/${id}`),

  updatePlanSection: (planId, sectionId, data) => client.put(`/plan/${planId}/section/${sectionId}`, data),

  updatePlanStatus: (id, status) => client.put(`/plan/${id}/status`, { status }),

  getCompliance: (planId) => client.get(`/plan/${planId}/compliance`),

  exportPlan: (id) => client.get(`/plan/${id}/export`, { responseType: 'blob' }),

  // Dashboard
  getOverview: () => client.get('/dashboard/overview'),

  getGaps: (rfpId) => client.get(`/dashboard/gaps/${rfpId}`),

  getRisks: (rfpId) => client.get(`/dashboard/risks/${rfpId}`),

  getRecommendations: (rfpId) => client.get(`/dashboard/recommendations/${rfpId}`),

  getSummary: () => client.get('/dashboard/summary'),

  // AI Draft Framework
  generateOutline: (planId) => client.post(`/ai/outline/${planId}`),

  generateInsertBlock: (planId, sectionId) => client.post(`/ai/insert-block/${planId}/${sectionId}`),

  generateComparison: (planId, sectionId) => client.post(`/ai/comparison/${planId}/${sectionId}`),

  generateJustification: (planId, sectionId) => client.post(`/ai/justification/${planId}/${sectionId}`),

  generateDraftFramework: (planId) => client.post(`/ai/draft-framework/${planId}`)
}

export default client
