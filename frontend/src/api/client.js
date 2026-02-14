import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000
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
  // ============================================================================
  // Boilerplate Manager (Module 1) - prefix: /api/boilerplate
  // ============================================================================
  getCategories: (params) => client.get('/boilerplate/categories', { params }),

  createCategory: (data) => client.post('/boilerplate/categories', data),

  getSections: (params) => client.get('/boilerplate/sections', { params }),

  getSection: (id) => client.get(`/boilerplate/sections/${id}`),

  createSection: (data) => client.post('/boilerplate/sections', data),

  updateSection: (id, data) => client.put(`/boilerplate/sections/${id}`, data),

  deleteSection: (id) => client.delete(`/boilerplate/sections/${id}`),

  getSectionVersions: (sectionId) => client.get(`/boilerplate/sections/${sectionId}/versions`),

  restoreSectionVersion: (sectionId, versionNumber) =>
    client.post(`/boilerplate/sections/${sectionId}/restore/${versionNumber}`),

  getTags: () => client.get('/boilerplate/tags'),

  createTag: (data) => client.post('/boilerplate/tags', data),

  searchBoilerplate: (query, params) =>
    client.get('/boilerplate/search', { params: { q: query, ...params } }),

  exportBoilerplate: () => client.get('/boilerplate/export'),

  importBoilerplate: (data) => client.post('/boilerplate/import', data),

  // ============================================================================
  // RFP Upload & Parse (Module 2) - prefix: /api/rfp
  // ============================================================================
  uploadRFP: (file, metadata = {}) => {
    const formData = new FormData()
    formData.append('file', file)
    // Append optional metadata as query params
    const params = {}
    if (metadata.title) params.title = metadata.title
    if (metadata.funder_name) params.funder_name = metadata.funder_name
    if (metadata.deadline) params.deadline = metadata.deadline
    if (metadata.funding_amount) params.funding_amount = metadata.funding_amount
    return client.post('/rfp/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params
    })
  },

  listRFPs: (params) => client.get('/rfp/', { params }),

  getRFP: (id) => client.get(`/rfp/${id}`),

  getRequirements: (rfpId) => client.get(`/rfp/${rfpId}/requirements`),

  updateRequirement: (rfpId, reqId, data) =>
    client.put(`/rfp/${rfpId}/requirements/${reqId}`, data),

  getRawText: (rfpId) => client.get(`/rfp/${rfpId}/raw-text`),

  reparseRFP: (rfpId) => client.post(`/rfp/${rfpId}/reparse`),

  deleteRFP: (id) => client.delete(`/rfp/${id}`),

  // ============================================================================
  // Crosswalk Engine (Module 3) - prefix: /api/crosswalk
  // ============================================================================
  generateCrosswalk: (rfpId) => client.post(`/crosswalk/generate/${rfpId}`),

  getCrosswalk: (rfpId, params) => client.get(`/crosswalk/${rfpId}`, { params }),

  getCrosswalkMatrix: (rfpId) => client.get(`/crosswalk/${rfpId}/matrix`),

  updateCrosswalkMapping: (mapId, data) => client.put(`/crosswalk/map/${mapId}`, data),

  approveCrosswalkMapping: (mapId) => client.post(`/crosswalk/map/${mapId}/approve`),

  regenerateCrosswalk: (rfpId) => client.post(`/crosswalk/${rfpId}/regenerate`),

  exportCrosswalk: (rfpId, format = 'json') =>
    client.get(`/crosswalk/${rfpId}/export`, { params: { format } }),

  getCrosswalkSummary: (rfpId) => client.get(`/crosswalk/${rfpId}/summary`),

  // ============================================================================
  // Grant Plan Generator (Module 4) - prefix: /api/plans
  // ============================================================================
  generatePlan: (rfpId, planTitle) =>
    client.post(`/plans/generate/${rfpId}`, null, { params: planTitle ? { plan_title: planTitle } : {} }),

  listPlans: (params) => client.get('/plans/', { params }),

  getPlan: (id) => client.get(`/plans/${id}`),

  getPlanSections: (planId) => client.get(`/plans/${planId}/sections`),

  updatePlanSection: (planId, sectionId, data) =>
    client.put(`/plans/${planId}/sections/${sectionId}`, data),

  updatePlanStatus: (planId, status) =>
    client.put(`/plans/${planId}/status`, null, { params: { status } }),

  getPlanCompliance: (planId) => client.get(`/plans/${planId}/compliance`),

  exportPlan: (planId, format = 'json') =>
    client.get(`/plans/${planId}/export`, { params: { format } }),

  deletePlan: (planId) => client.delete(`/plans/${planId}`),

  // ============================================================================
  // Dashboard (Module 5) - prefix: /api/dashboard
  // ============================================================================
  getDashboardOverview: (rfpId) => client.get(`/dashboard/${rfpId}/overview`),

  getDashboardSummary: () => client.get('/dashboard/summary'),

  getGapAnalysis: (rfpId) => client.get(`/dashboard/${rfpId}/gaps`),

  getRiskDistribution: (rfpId) => client.get(`/dashboard/${rfpId}/risks`),

  getAlignmentScores: (rfpId) => client.get(`/dashboard/${rfpId}/scores`),

  getRecommendations: (rfpId, priority) =>
    client.get(`/dashboard/${rfpId}/recommendations`, { params: priority ? { priority } : {} }),

  getRiskTimeline: (rfpId) => client.get(`/dashboard/${rfpId}/timeline`),

  // ============================================================================
  // AI Draft Framework (Module 6) - prefix: /api/ai
  // ============================================================================
  generateOutline: (planId, params = {}) =>
    client.post(`/ai/outline/${planId}`, null, { params }),

  generateInsertBlock: (params) =>
    client.post('/ai/insert-block', null, { params }),

  generateComparison: (params) =>
    client.post('/ai/comparison', null, { params }),

  generateJustification: (params) =>
    client.post('/ai/justification', null, { params }),

  generateDraftFramework: (planId, params = {}) =>
    client.post(`/ai/draft-framework/${planId}`, null, { params }),

  getSavedDrafts: (planId, blockType) =>
    client.get(`/ai/drafts/${planId}`, { params: blockType ? { block_type: blockType } : {} })
}

export default client
