import { create } from 'zustand'

const useAuthStore = create((set, get) => ({
  // State
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  loading: false,
  error: null,

  // Actions
  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),
  setError: (error) => set({ error }),

  login: (user, token, refreshToken) => {
    localStorage.setItem('authToken', token)
    localStorage.setItem('refreshToken', refreshToken)
    localStorage.setItem('authUser', JSON.stringify(user))
    set({
      user,
      token,
      refreshToken,
      isAuthenticated: true,
      error: null,
    })
  },

  logout: () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('authUser')
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      error: null,
    })
  },

  updateToken: (token, refreshToken) => {
    localStorage.setItem('authToken', token)
    if (refreshToken) {
      localStorage.setItem('refreshToken', refreshToken)
    }
    set({
      token,
      ...(refreshToken ? { refreshToken } : {}),
    })
  },

  loadFromStorage: () => {
    const token = localStorage.getItem('authToken')
    const refreshToken = localStorage.getItem('refreshToken')
    const userStr = localStorage.getItem('authUser')

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr)
        set({
          user,
          token,
          refreshToken,
          isAuthenticated: true,
        })
        return true
      } catch {
        // Corrupted data — clear it
        localStorage.removeItem('authToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('authUser')
      }
    }
    return false
  },

  setLoading: (loading) => set({ loading }),
}))

export default useAuthStore
