import { useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Database,
  FileUp,
  GitCompare,
  FileText,
  Shield,
  Sparkles,
  Menu,
  X,
  Bell
} from 'lucide-react'
import useAppStore from '../stores/appStore'
import clsx from 'clsx'

const modules = [
  { id: 'dashboard', name: 'Dashboard', path: '/', icon: LayoutDashboard, badge: null },
  { id: 'boilerplate', name: 'Boilerplate Manager', path: '/boilerplate', icon: Database, badge: null },
  { id: 'rfp', name: 'RFP Upload & Parse', path: '/rfp', icon: FileUp, badge: 'pending' },
  { id: 'crosswalk', name: 'Crosswalk Engine', path: '/crosswalk', icon: GitCompare, badge: null },
  { id: 'plan', name: 'Grant Plan Generator', path: '/plan', icon: FileText, badge: null },
  { id: 'gaps-risks', name: 'Gap & Risk Dashboard', path: '/gaps-risks', icon: Shield, badge: null },
  { id: 'ai-framework', name: 'AI Draft Framework', path: '/ai-framework', icon: Sparkles, badge: null }
]

export default function Sidebar({ open, setOpen }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { notificationCount } = useAppStore()

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
        <div className="w-64 h-full bg-foam-primary text-white shadow-xl overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                <span className="font-bold text-foam-primary text-lg">F</span>
              </div>
              <div>
                <h1 className="text-xl font-bold">FOAM</h1>
                <p className="text-xs text-blue-100">Grant Engine</p>
              </div>
            </div>

            <nav className="space-y-2">
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
                      'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left',
                      active
                        ? 'bg-blue-600 text-white'
                        : 'text-blue-100 hover:bg-foam-secondary'
                    )}
                  >
                    <Icon size={20} />
                    <span className="flex-1 font-medium">{module.name}</span>
                    {pendingCount > 0 && (
                      <span className="bg-foam-amber text-foam-primary text-xs font-bold px-2 py-1 rounded-full">
                        {pendingCount}
                      </span>
                    )}
                  </button>
                )
              })}
            </nav>
          </div>

          <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-blue-500">
            <div className="bg-blue-600 rounded-lg p-4">
              <h3 className="font-semibold text-sm mb-2">Organization</h3>
              <p className="text-xs text-blue-100 leading-relaxed">
                Fathers On A Mission (FOAM)
                <br />
                Baton Rouge, LA
                <br />
                Executive Director: Levar Robinson
              </p>
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
