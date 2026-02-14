import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Database,
  FileUp,
  GitCompare,
  FileText,
  Shield,
  Sparkles,
  ArrowLeft,
  SearchCheck
} from 'lucide-react'
import useAppStore from '../stores/appStore'
import { apiClient } from '../api/client'
import clsx from 'clsx'

const modules = [
  { id: 'dashboard', name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { id: 'boilerplate', name: 'Boilerplate', path: '/boilerplate', icon: Database },
  { id: 'rfp', name: 'RFP Upload', path: '/rfp', icon: FileUp },
  { id: 'crosswalk', name: 'Crosswalk', path: '/crosswalk', icon: GitCompare },
  { id: 'plan', name: 'Grant Plans', path: '/plan', icon: FileText },
  { id: 'gaps-risks', name: 'Gaps & Risks', path: '/gaps-risks', icon: Shield },
  { id: 'ai-framework', name: 'AI Drafts', path: '/ai-framework', icon: Sparkles },
  { id: 'funding-research', name: 'Funding Research', path: '/funding-research', icon: SearchCheck }
]

export default function Sidebar({ open, setOpen }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { notificationCount } = useAppStore()
  const [grantCount, setGrantCount] = useState(0)
  const [boilerplateCount, setBoilerplateCount] = useState(0)

  // Fetch live counts
  useEffect(() => {
    async function fetchCounts() {
      try {
        const [plansRes, sectionsRes] = await Promise.allSettled([
          apiClient.listPlans(),
          apiClient.getSections()
        ])
        if (plansRes.status === 'fulfilled') {
          const data = plansRes.value.data
          const list = Array.isArray(data) ? data : (data.plans || data.items || [])
          setGrantCount(list.length)
        }
        if (sectionsRes.status === 'fulfilled') {
          const data = sectionsRes.value.data
          const list = Array.isArray(data) ? data : (data.sections || data.items || [])
          setBoilerplateCount(list.length)
        }
      } catch (err) {
        console.log('Sidebar counts unavailable:', err.message)
      }
    }
    fetchCounts()
  }, [location.pathname])

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  return (
    <>
      <div
        className={clsx(
          'fixed inset-y-0 left-0 z-40 transition-transform duration-300 lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="w-48 h-full bg-brand-primary text-white shadow-xl overflow-y-auto flex flex-col">
          <div className="p-4 flex-1">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                <span className="font-bold text-brand-primary text-sm">G</span>
              </div>
              <div>
                <h1 className="text-base font-bold leading-tight">GAE</h1>
                <p className="text-[10px] text-blue-100">Grant Engine</p>
              </div>
            </div>

            <button
              onClick={() => {
                navigate('/')
                setOpen(false)
              }}
              className="flex items-center gap-2 px-3 py-2 mb-3 rounded-lg bg-white/10 hover:bg-white/20 text-blue-100 hover:text-white transition-colors text-xs font-medium w-full"
            >
              <ArrowLeft size={14} />
              Dashboard
            </button>

            <nav className="space-y-1">
              {modules.map((module) => {
                const Icon = module.icon
                const active = isActive(module.path)
                const pendingCount = module.id === 'rfp' ? notificationCount : 0

                return (
                  <button
                    key={module.id}
                    onClick={() => {
                      navigate(module.path)
                      setOpen(false)
                    }}
                    className={clsx(
                      'w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors text-left text-xs',
                      active
                        ? 'bg-blue-600 text-white'
                        : 'text-blue-100 hover:bg-brand-secondary'
                    )}
                  >
                    <Icon size={16} />
                    <span className="flex-1 font-medium">{module.name}</span>
                    {pendingCount > 0 && (
                      <span className="bg-brand-amber text-brand-primary text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                        {pendingCount}
                      </span>
                    )}
                  </button>
                )
              })}
            </nav>
          </div>

          {/* Live Counters - replaces Organization block */}
          <div className="p-4 border-t border-blue-500">
            <div className="space-y-2">
              <div className="bg-blue-600/60 rounded-lg p-3 flex items-center gap-2">
                <FileText size={16} className="text-blue-200 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-lg font-bold leading-tight">{grantCount}</p>
                  <p className="text-[10px] text-blue-200 leading-tight">Active Grants</p>
                </div>
              </div>
              <div className="bg-blue-600/60 rounded-lg p-3 flex items-center gap-2">
                <Database size={16} className="text-blue-200 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-lg font-bold leading-tight">{boilerplateCount}</p>
                  <p className="text-[10px] text-blue-200 leading-tight">Boilerplate Sections</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {open && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}
    </>
  )
}
