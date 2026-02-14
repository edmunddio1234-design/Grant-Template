import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TrendingUp, FileText, Zap, Target, Upload, Plus } from 'lucide-react'
import StatusIndicator from '../components/common/StatusIndicator'
import RiskBadge from '../components/common/RiskBadge'
import GrantFunderChart from '../components/GrantFunderChart'
import useAppStore from '../stores/appStore'
import { apiClient } from '../api/client'

const emptyDashboardData = {
  stats: [
    { label: 'Total Boilerplate Sections', value: 0, icon: Target, color: 'bg-blue-50 text-brand-primary' },
    { label: 'Active RFPs', value: 0, icon: FileText, color: 'bg-green-50 text-brand-green' },
    { label: 'Pending Crosswalks', value: 0, icon: TrendingUp, color: 'bg-amber-50 text-brand-amber' },
    { label: 'Plans Generated', value: 0, icon: Zap, color: 'bg-purple-50 text-purple-600' }
  ],
  recentRFPs: [],
  activityFeed: []
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { setDashboardLoading } = useAppStore()
  const [dashboardData, setDashboardData] = useState(emptyDashboardData)
  const [loading, setLoading] = useState(true)
  const [apiConnected, setApiConnected] = useState(false)

  useEffect(() => {
    async function fetchDashboard() {
      setDashboardLoading(true)
      setLoading(true)
      try {
        const summaryRes = await apiClient.getDashboardSummary()
        const summary = summaryRes.data

        const apiData = {
          stats: [
            { label: 'Total Boilerplate Sections', value: summary.total_boilerplate_sections ?? 0, icon: Target, color: 'bg-blue-50 text-brand-primary' },
            { label: 'Active RFPs', value: summary.active_rfps ?? 0, icon: FileText, color: 'bg-green-50 text-brand-green' },
            { label: 'Pending Crosswalks', value: summary.pending_crosswalks ?? 0, icon: TrendingUp, color: 'bg-amber-50 text-brand-amber' },
            { label: 'Plans Generated', value: summary.plans_generated ?? 0, icon: Zap, color: 'bg-purple-50 text-purple-600' }
          ],
          recentRFPs: summary.recent_rfps || [],
          activityFeed: summary.activity_feed || []
        }
        setDashboardData(apiData)
        setApiConnected(true)
      } catch (err) {
        console.log('Dashboard API unavailable, showing empty state:', err.message)
        setDashboardData(emptyDashboardData)
        setApiConnected(false)
      } finally {
        setDashboardLoading(false)
        setLoading(false)
      }
    }
    fetchDashboard()
  }, [])

  const statusConfig = {
    uploaded: 'pending',
    parsing: 'loading',
    parsed: 'active',
    analyzing: 'loading',
    analyzed: 'active',
    archived: 'error'
  }

  return (
    <div className="p-6 space-y-8">
      {/* Grant Funder Analytics — animated background chart */}
      <GrantFunderChart />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {dashboardData.stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <div key={index} className="card-hover">
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  </div>
                  <div className={`p-3 rounded-lg ${stat.color}`}>
                    <Icon size={24} />
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3">
        <button className="btn-primary" onClick={() => navigate('/rfp')}>
          <Upload size={20} />
          Upload RFP
        </button>
        <button className="btn-secondary" onClick={() => navigate('/boilerplate')}>
          <Plus size={20} />
          New Boilerplate Section
        </button>
      </div>

      {/* Recent Activity — only show if we have real data */}
      {dashboardData.activityFeed.length > 0 && (
        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <h3 className="subsection-title">Recent Activity</h3>
            <p className="text-sm text-gray-600 mt-1">Last {dashboardData.activityFeed.length} actions</p>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {dashboardData.activityFeed.map((activity, idx) => (
                <div key={activity.id || idx} className="flex gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
                  <div className="w-2 h-2 bg-brand-primary rounded-full mt-2 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 text-sm">{activity.action}</p>
                    <p className="text-sm text-gray-600 truncate">{activity.description}</p>
                    <p className="text-xs text-gray-500 mt-1">{activity.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Recent RFPs Table — only show if we have real data */}
      {dashboardData.recentRFPs.length > 0 && (
        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <h3 className="subsection-title">Recent RFPs</h3>
            <p className="text-sm text-gray-600 mt-1">Latest uploaded and processed RFPs</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="table-header">RFP Name</th>
                  <th className="table-header">Upload Date</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Requirements</th>
                  <th className="table-header">Alignment Score</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.recentRFPs.map((rfp, idx) => (
                  <tr key={rfp.id || idx} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                    <td className="table-cell font-medium text-gray-900">{rfp.name || rfp.title}</td>
                    <td className="table-cell text-gray-600">{rfp.uploadDate || rfp.upload_date}</td>
                    <td className="table-cell">
                      <StatusIndicator status={statusConfig[rfp.status]} size="sm" />
                    </td>
                    <td className="table-cell text-gray-600">{rfp.requirements}</td>
                    <td className="table-cell">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-brand-primary rounded-full transition-all" style={{ width: `${rfp.alignmentScore || rfp.alignment_score || 0}%` }} />
                        </div>
                        <span className="text-sm font-medium text-gray-900">{rfp.alignmentScore || rfp.alignment_score || 0}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Key Metrics — only show when API provides real data */}
      {apiConnected && dashboardData.recentRFPs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card">
            <div className="p-6">
              <h4 className="font-semibold text-gray-900 mb-4">Next Steps</h4>
              <ul className="space-y-3 text-sm">
                <li className="flex gap-2">
                  <span className="text-brand-amber font-bold">1.</span>
                  <span className="text-gray-700">Review uploaded RFP analysis</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-brand-amber font-bold">2.</span>
                  <span className="text-gray-700">Run crosswalk alignment</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-brand-amber font-bold">3.</span>
                  <span className="text-gray-700">Generate grant plan</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-brand-amber font-bold">4.</span>
                  <span className="text-gray-700">Export draft frameworks</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
