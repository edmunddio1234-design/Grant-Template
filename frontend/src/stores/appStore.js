import { create } from 'zustand'

const useAppStore = create((set, get) => ({
  // RFP State
  currentRFP: null,
  rfpList: [],
  rfpLoading: false,

  // Boilerplate State
  boilerplateSections: [],
  boilerplateCategories: [],
  boilerplateLoading: false,
  boilerplateFilters: {
    category: null,
    tags: [],
    search: ''
  },

  // Crosswalk State
  currentCrosswalk: null,
  crosswalkMatrix: null,
  crosswalkLoading: false,

  // Plan State
  currentPlan: null,
  planList: [],
  planLoading: false,

  // Dashboard State
  dashboardData: null,
  dashboardLoading: false,

  // UI State
  sidebarCollapsed: false,
  activeModule: 'dashboard',
  loadingStates: {},
  notificationCount: 0,

  // RFP Actions
  setCurrentRFP: (rfp) => set({ currentRFP: rfp }),
  setRFPList: (list) => set({ rfpList: list }),
  setRFPLoading: (loading) => set({ rfpLoading: loading }),
  addRFP: (rfp) => set((state) => ({
    rfpList: [rfp, ...state.rfpList]
  })),

  // Boilerplate Actions
  setBoilerplateSections: (sections) => set({ boilerplateSections: sections }),
  setBoilerplateCategories: (categories) => set({ boilerplateCategories: categories }),
  setBoilerplateLoading: (loading) => set({ boilerplateLoading: loading }),
  setBoilerplateFilters: (filters) => set((state) => ({
    boilerplateFilters: { ...state.boilerplateFilters, ...filters }
  })),
  addBoilerplateSection: (section) => set((state) => ({
    boilerplateSections: [section, ...state.boilerplateSections]
  })),
  updateBoilerplateSection: (id, updates) => set((state) => ({
    boilerplateSections: state.boilerplateSections.map((s) =>
      s.id === id ? { ...s, ...updates } : s
    )
  })),
  removeBoilerplateSection: (id) => set((state) => ({
    boilerplateSections: state.boilerplateSections.filter((s) => s.id !== id)
  })),

  // Crosswalk Actions
  setCurrentCrosswalk: (crosswalk) => set({ currentCrosswalk: crosswalk }),
  setCrosswalkMatrix: (matrix) => set({ crosswalkMatrix: matrix }),
  setCrosswalkLoading: (loading) => set({ crosswalkLoading: loading }),
  updateCrosswalkMapping: (mappingId, updates) => set((state) => ({
    crosswalkMatrix: state.crosswalkMatrix ? {
      ...state.crosswalkMatrix,
      mappings: state.crosswalkMatrix.mappings.map((m) =>
        m.id === mappingId ? { ...m, ...updates } : m
      )
    } : null
  })),

  // Plan Actions
  setCurrentPlan: (plan) => set({ currentPlan: plan }),
  setPlanList: (list) => set({ planList: list }),
  setPlanLoading: (loading) => set({ planLoading: loading }),
  addPlan: (plan) => set((state) => ({
    planList: [plan, ...state.planList]
  })),
  updateCurrentPlan: (updates) => set((state) => ({
    currentPlan: state.currentPlan ? { ...state.currentPlan, ...updates } : null
  })),

  // Dashboard Actions
  setDashboardData: (data) => set({ dashboardData: data }),
  setDashboardLoading: (loading) => set({ dashboardLoading: loading }),

  // UI Actions
  toggleSidebar: () => set((state) => ({
    sidebarCollapsed: !state.sidebarCollapsed
  })),
  setActiveModule: (module) => set({ activeModule: module }),
  setLoadingState: (key, loading) => set((state) => ({
    loadingStates: { ...state.loadingStates, [key]: loading }
  })),
  setNotificationCount: (count) => set({ notificationCount: count }),

  // Clear State
  clearAllState: () => set({
    currentRFP: null,
    rfpList: [],
    rfpLoading: false,
    boilerplateSections: [],
    boilerplateCategories: [],
    boilerplateLoading: false,
    boilerplateFilters: {
      category: null,
      tags: [],
      search: ''
    },
    currentCrosswalk: null,
    crosswalkMatrix: null,
    crosswalkLoading: false,
    currentPlan: null,
    planList: [],
    planLoading: false,
    dashboardData: null,
    dashboardLoading: false,
    sidebarCollapsed: false,
    activeModule: 'dashboard',
    loadingStates: {},
    notificationCount: 0
  })
}))

export default useAppStore
