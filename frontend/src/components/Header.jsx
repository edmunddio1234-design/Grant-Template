import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Menu, Search, Bell, ChevronDown, LogOut } from 'lucide-react'
import useAppStore from '../stores/appStore'
import useAuthStore from '../stores/authStore'
import clsx from 'clsx'

const pageNames = {
  '/': 'Dashboard',
  '/boilerplate': 'Boilerplate Manager',
  '/rfp': 'RFP Upload & Parse',
  '/crosswalk': 'Crosswalk Engine',
  '/plan': 'Grant Plan Generator',
  '/gaps-risks': 'Gap & Risk Dashboard',
  '/ai-framework': 'AI Draft Framework'
}

const roleLabels = {
  admin: 'Admin',
  grant_manager: 'Grant Manager',
  reviewer: 'Reviewer',
  viewer: 'Viewer',
}

export default function Header({ onMenuClick }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { notificationCount } = useAppStore()
  const { user, logout } = useAuthStore()
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)

  const pageName = pageNames[location.pathname] || 'Dashboard'

  const userName = user?.name || 'User'
  const userRole = roleLabels[user?.role] || user?.role || 'User'
  const initials = userName
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  const handleLogout = () => {
    logout()
    setUserMenuOpen(false)
    navigate('/login')
  }

  return (
    <header className="border-b border-gray-200 bg-white shadow-sm sticky top-0 z-30">
      <div className="flex items-center justify-between h-16 px-6 gap-4">
        <div className="flex items-center gap-4 flex-1">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Menu size={20} className="text-gray-600" />
          </button>

          <h1 className="text-2xl font-bold text-gray-900">{pageName}</h1>
        </div>

        <div className="flex items-center gap-4">
          <div className={clsx(
            'transition-all duration-300',
            searchOpen ? 'w-48' : 'w-10'
          )}>
            <div className="relative">
              <Search
                size={20}
                className={clsx(
                  'absolute left-3 top-1/2 -translate-y-1/2 transition-colors',
                  searchOpen ? 'text-brand-primary' : 'text-gray-400'
                )}
              />
              <input
                type="text"
                placeholder="Search..."
                className={clsx(
                  'w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent transition-all',
                  !searchOpen && 'opacity-0'
                )}
                onFocus={() => setSearchOpen(true)}
                onBlur={() => setSearchOpen(false)}
              />
            </div>
          </div>

          <div className="relative">
            <button className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600">
              <Bell size={20} />
              {notificationCount > 0 && (
                <span className="absolute top-1 right-1 w-5 h-5 bg-brand-red text-white text-xs rounded-full flex items-center justify-center font-bold">
                  {notificationCount > 9 ? '9+' : notificationCount}
                </span>
              )}
            </button>
          </div>

          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 px-3 py-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <div className="w-8 h-8 bg-brand-primary rounded-full flex items-center justify-center text-white font-bold text-sm">
                {initials}
              </div>
              <ChevronDown size={18} className="text-gray-600" />
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-2 z-50">
                <div className="px-4 py-2 border-b border-gray-100">
                  <p className="font-semibold text-sm text-gray-900">{userName}</p>
                  <p className="text-xs text-gray-500">{userRole}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2 transition-colors"
                >
                  <LogOut size={16} />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
