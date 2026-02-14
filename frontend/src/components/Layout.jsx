import { useState } from 'react'
import Sidebar from './Sidebar'
import Header from './Header'

export default function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />

      {/* lg:ml-48 offsets the fixed sidebar (w-48 = 12rem) so content never overlaps */}
      <div className="flex flex-col flex-1 overflow-hidden lg:ml-48">
        <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />

        <main className="flex-1 overflow-auto">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>

        <footer className="border-t border-gray-200 bg-white px-6 py-4">
          <p className="text-sm text-gray-600">
            Grant Alignment Engine © 2025. All rights reserved.
          </p>
        </footer>
      </div>
    </div>
  )
}
