import { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import BoilerplateManager from './pages/BoilerplateManager'
import RFPUpload from './pages/RFPUpload'
import CrosswalkEngine from './pages/CrosswalkEngine'
import GrantPlanGenerator from './pages/GrantPlanGenerator'
import GapRiskDashboard from './pages/GapRiskDashboard'
import AIDraftFramework from './pages/AIDraftFramework'
import useAppStore from './stores/appStore'
import useAuthStore from './stores/authStore'

function App() {
  const { setDashboardLoading } = useAppStore()
  const { loadFromStorage } = useAuthStore()

  useEffect(() => {
    loadFromStorage()
    setDashboardLoading(true)
    setDashboardLoading(false)
  }, [])

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/boilerplate" element={<BoilerplateManager />} />
                <Route path="/rfp" element={<RFPUpload />} />
                <Route path="/crosswalk" element={<CrosswalkEngine />} />
                <Route path="/plan" element={<GrantPlanGenerator />} />
                <Route path="/gaps-risks" element={<GapRiskDashboard />} />
                <Route path="/ai-framework" element={<AIDraftFramework />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
