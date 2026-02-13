import { useEffect, useState } from 'react'
import { BarChart, Bar, PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, FileText, Zap, Target, Upload, Plus } from 'lucide-react'
import StatusIndicator from '../components/common/StatusIndicator'
import RiskBadge from '../components/common/RiskBadge'
import useAppStore from '../stores/appStore'

const mockDashboardData = {
  stats: [
    { label: 'Total Boilerplate Sections', value: 47, icon: Target, color: 'bg-blue-50 text-foam-primary' },
    { label: 'Active RFPs', value: 3, icon: FileText, color: 'bg-green-50 text-foam-green' },
    { label: 'Pending Crosswalks', value: 2, icon: TrendingUp, color: 'bg-amber-50 text-foam-amber' },
    { label: 'Plans Generated', value: 8, icon: Zap, color: 'bg-purple-50 text-purple-600' }
  ],
  riskDistribution: [
    { name: 'Low Risk', value: 12, fill: '#22C55E' },
    { name: 'Medium Risk', value: 6, fill: '#F59E0B' },
    { name: 'High Risk', value: 2, fill: '#EF4444' }
  ],
  recentRFPs: [
    {
      id: 1,
      name: 'Community Foundation Grant 2024',
      uploadDate: '2024-02-10',
      status: 'parsed',
      requirements: 23,
      alignmentScore: 78
    },
    {
      id: 2,
      name: 'Department of Family Services RFP',
      uploadDate: '2024-02-08',
      status: 'analyzing',
      requirements: 31,
      alignmentScore: 65
    },
    {
      id: 3,
      name: 'Local Nonprofit Partnership Grant',
      uploadDate: '2024-02-05',
      status: 'uploaded',
      requirements: 18,
      alignmentScore: 82
    }
  ],
  activityFeed: [
    { id: 1, action: 'Uploaded RFP', description: 'Community Foundation Grant 2024', timestamp: '2 hours ago' },
    { id: 2, action: 'Generated Plan', description: 'DFS Grant - Project Family Build Track', timestamp: '5 hours ago' },
    { id: 3, action: 'Updated Section', description: 'Organizational Capacity - added 2 new examples', timestamp: '1 day ago' },
    { id: 4, action: 'Crosswalk Complete', description: 'Nonprofit Partnership alignment analysis finished', timestamp: '2 days ago' }
  ]
}

export default function Dashboard() {
  const { setDashboardLoading } = useAppStore()
  const [dashboardData] = useState(mockDashboardData)

  useEffect(() => {
    setDashboardLoading(true)
    const timer = setTimeout(() => setDashboardLoading(false), 500)
    return () => clearTimeout(timer)
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
        <button className="btn-primary">
          <Upload size={20} />
          Upload RFP
        </button>
        <button className="btn-secondary">
          <Plus size={20} />
          New Boilerplate Section
        </button>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <h3 className="subsection-title">Risk Distribution</h3>
            <p className="text-sm text-gray-600 mt-1">Across all active RFPs</p>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={dashboardData.riskDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {dashboardData.riskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <h3 className="subsection-title">Recent Activity</h3>
            <p className="text-sm text-gray-600 mt-1">Last 4 actions</p>
          </div>
          <div className="p-6 space-y-4">
            {dashboardData.activityFeed.map((activity) => (
              <div key={activity.id} className="flex gap-4 pb-4 border-b border-gray-100 last:border-b-0 last:pb-0">
                <div className="w-2 h-2 bg-foam-primary rounded-full mt-2 flex-shrink-0" />
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

      {/* Recent RFPs Table */}
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
              {dashboardData.recentRFPs.map((rfp) => (
                <tr key={rfp.id} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                  <td className="table-cell font-medium text-gray-900">{rfp.name}</td>
                  <td className="table-cell text-gray-600">{rfp.uploadDate}</td>
                  <td className="table-cell">
                    <StatusIndicator status={statusConfig[rfp.status]} size="sm" />
                  </td>
                  <td className="table-cell text-gray-600">{rfp.requirements}</td>
                  <td className="table-cell">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-foam-primary rounded-full transition-all"
                          style={{ width: `${rfp.alignmentScore}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-900">{rfp.alignmentScore}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="p-6">
            <h4 className="font-semibold text-gray-900 mb-4">Boilerplate Coverage</h4>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">Program Specific</span>
                  <span className="text-sm font-semibold text-gray-900">92%</span>
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-foam-green w-[92%]" />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">Evidence Based</span>
                  <span className="text-sm font-semibold text-gray-900">78%</span>
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-foam-amber w-[78%]" />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">Data Complete</span>
                  <span className="text-sm font-semibold text-gray-900">85%</span>
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-foam-primary w-[85%]" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="p-6">
            <h4 className="font-semibold text-gray-900 mb-4">RFP Status Breakdown</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Uploaded</span>
                <RiskBadge level="yellow" label="1" showIcon={false} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Parsing/Analyzing</span>
                <RiskBadge level="yellow" label="1" showIcon={false} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Ready for Planning</span>
                <RiskBadge level="green" label="1" showIcon={false} />
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="p-6">
            <h4 className="font-semibold text-gray-900 mb-4">Next Steps</h4>
            <ul className="space-y-3 text-sm">
              <li className="flex gap-2">
                <span className="text-foam-amber font-bold">1.</span>
                <span className="text-gray-700">Review DFS RFP analysis</span>
              </li>
              <li className="flex gap-2">
                <span className="text-foam-amber font-bold">2.</span>
                <span className="text-gray-700">Generate Project Family Build Plan</span>
              </li>
              <li className="flex gap-2">
                <span className="text-foam-amber font-bold">3.</span>
                <span className="text-gray-700">Complete 2 pending crosswalks</span>
              </li>
              <li className="flex gap-2">
                <span className="text-foam-amber font-bold">4.</span>
                <span className="text-gray-700">Export 3 draft frameworks</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
