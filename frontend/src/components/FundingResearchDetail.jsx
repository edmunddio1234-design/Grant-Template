import { useState, useEffect } from 'react'
import {
  X, Building2, DollarSign, Users, BarChart3, Globe,
  FileText, Award, ChevronRight, ExternalLink, Loader2,
  MapPin, Calendar, Hash, TrendingUp, TrendingDown
} from 'lucide-react'
import { apiClient } from '../api/client'
import toast from 'react-hot-toast'

const TABS = [
  { id: 'overview', label: 'Overview', icon: Building2 },
  { id: 'financials', label: 'Financials', icon: BarChart3 },
  { id: 'awards', label: 'Awards', icon: Award },
  { id: 'people', label: 'People', icon: Users },
  { id: 'peers', label: 'Peers', icon: Globe },
]

function formatCurrency(val) {
  if (val == null) return '—'
  return '$' + Number(val).toLocaleString(undefined, { maximumFractionDigits: 0 })
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString()
}

// ============================================================================
// OVERVIEW TAB
// ============================================================================
function OverviewTab({ org }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Mission & Details */}
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-1">Mission</h4>
            <p className="text-gray-800 leading-relaxed">
              {org.mission || 'No mission statement available.'}
            </p>
          </div>
          {org.address_line1 && (
            <div className="flex items-start gap-2 text-sm text-gray-600">
              <MapPin className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{org.address_line1}, {org.city}, {org.state} {org.zip}</span>
            </div>
          )}
          {org.website && (
            <div className="flex items-center gap-2 text-sm">
              <Globe className="w-4 h-4 text-gray-400" />
              <a href={org.website.startsWith('http') ? org.website : `https://${org.website}`}
                 target="_blank" rel="noopener noreferrer"
                 className="text-blue-600 hover:underline">
                {org.website}
              </a>
            </div>
          )}
        </div>

        {/* Right: Key Stats */}
        <div className="space-y-3">
          <StatCard label="Latest Revenue" value={formatCurrency(org.revenue_latest)} icon={DollarSign} color="green" />
          <StatCard label="NTEE Code" value={org.ntee_code || '—'} icon={Hash} color="blue" />
          <StatCard label="Ruling Year" value={org.ruling_year || '—'} icon={Calendar} color="purple" />
          <StatCard label="EIN" value={org.ein} icon={FileText} color="gray" />
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, icon: Icon, color }) {
  const colorMap = {
    green: 'bg-green-50 text-green-700',
    blue: 'bg-blue-50 text-blue-700',
    purple: 'bg-purple-50 text-purple-700',
    gray: 'bg-gray-50 text-gray-700',
  }
  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg ${colorMap[color] || colorMap.gray}`}>
      <Icon className="w-5 h-5" />
      <div>
        <p className="text-xs opacity-70">{label}</p>
        <p className="font-semibold text-sm">{value}</p>
      </div>
    </div>
  )
}

// ============================================================================
// FINANCIALS TAB
// ============================================================================
function FinancialsTab({ filings }) {
  if (!filings.length) return <EmptyState message="No financial filings available." />

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-2 font-medium text-gray-500">Year</th>
            <th className="text-left py-3 px-2 font-medium text-gray-500">Form</th>
            <th className="text-right py-3 px-2 font-medium text-gray-500">Revenue</th>
            <th className="text-right py-3 px-2 font-medium text-gray-500">Expenses</th>
            <th className="text-right py-3 px-2 font-medium text-gray-500">Assets</th>
            <th className="text-right py-3 px-2 font-medium text-gray-500">Liabilities</th>
            <th className="text-center py-3 px-2 font-medium text-gray-500">PDF</th>
          </tr>
        </thead>
        <tbody>
          {filings.map((f, i) => (
            <tr key={`${f.tax_year}-${f.form_type}`}
                className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="py-2.5 px-2 font-medium">{f.tax_year}</td>
              <td className="py-2.5 px-2 text-gray-600">{f.form_type}</td>
              <td className="py-2.5 px-2 text-right">{formatCurrency(f.total_revenue)}</td>
              <td className="py-2.5 px-2 text-right">{formatCurrency(f.total_expenses)}</td>
              <td className="py-2.5 px-2 text-right">{formatCurrency(f.total_assets)}</td>
              <td className="py-2.5 px-2 text-right">{formatCurrency(f.total_liabilities)}</td>
              <td className="py-2.5 px-2 text-center">
                {f.pdf_url ? (
                  <a href={f.pdf_url} target="_blank" rel="noopener noreferrer"
                     className="text-blue-500 hover:text-blue-700">
                    <ExternalLink className="w-4 h-4 inline" />
                  </a>
                ) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ============================================================================
// AWARDS TAB
// ============================================================================
function AwardsTab({ awards }) {
  if (!awards.length) return <EmptyState message="No federal awards found." />

  const total = awards.reduce((sum, a) => sum + (a.amount || 0), 0)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{awards.length} awards found</p>
        <p className="text-lg font-bold text-green-700">{formatCurrency(total)} total</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-2 font-medium text-gray-500">Date</th>
              <th className="text-left py-3 px-2 font-medium text-gray-500">Agency</th>
              <th className="text-right py-3 px-2 font-medium text-gray-500">Amount</th>
              <th className="text-left py-3 px-2 font-medium text-gray-500">Type</th>
              <th className="text-left py-3 px-2 font-medium text-gray-500">Description</th>
            </tr>
          </thead>
          <tbody>
            {awards.slice(0, 50).map((a, i) => (
              <tr key={a.award_id}
                  className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="py-2.5 px-2 whitespace-nowrap">{formatDate(a.action_date)}</td>
                <td className="py-2.5 px-2 max-w-[200px] truncate">{a.awarding_agency || '—'}</td>
                <td className="py-2.5 px-2 text-right font-medium">{formatCurrency(a.amount)}</td>
                <td className="py-2.5 px-2">{a.award_type || '—'}</td>
                <td className="py-2.5 px-2 max-w-[250px] truncate text-gray-600">
                  {a.description || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ============================================================================
// PEOPLE TAB
// ============================================================================
function PeopleTab({ personnel }) {
  if (!personnel.length) return <EmptyState message="No personnel data available." />

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-2 font-medium text-gray-500">Name</th>
            <th className="text-left py-3 px-2 font-medium text-gray-500">Title</th>
            <th className="text-right py-3 px-2 font-medium text-gray-500">Compensation</th>
            <th className="text-center py-3 px-2 font-medium text-gray-500">Tax Year</th>
          </tr>
        </thead>
        <tbody>
          {personnel.map((p, i) => (
            <tr key={`${p.name}-${p.tax_year}`}
                className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="py-2.5 px-2 font-medium">{p.name}</td>
              <td className="py-2.5 px-2 text-gray-600">{p.title || '—'}</td>
              <td className="py-2.5 px-2 text-right">{formatCurrency(p.compensation)}</td>
              <td className="py-2.5 px-2 text-center text-gray-500">{p.tax_year}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ============================================================================
// PEERS TAB
// ============================================================================
function PeersTab({ peers, onSelectOrg }) {
  if (!peers.length) return <EmptyState message="No peer organizations found. Peers are matched by NTEE code, state, and revenue band." />

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {peers.map(peer => (
        <button
          key={peer.ein}
          onClick={() => onSelectOrg(peer.ein)}
          className="text-left p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all"
        >
          <h4 className="font-medium text-gray-900 text-sm truncate">{peer.name_legal}</h4>
          <p className="text-xs text-gray-500 mt-1">
            EIN {peer.ein} &bull; {peer.city}, {peer.state}
          </p>
          <p className="text-sm font-semibold text-green-700 mt-1">
            {formatCurrency(peer.revenue_latest)}
          </p>
        </button>
      ))}
    </div>
  )
}

// ============================================================================
// EMPTY STATE
// ============================================================================
function EmptyState({ message }) {
  return (
    <div className="text-center py-8 text-gray-400">
      <FileText className="w-10 h-10 mx-auto mb-2 opacity-50" />
      <p className="text-sm">{message}</p>
    </div>
  )
}

// ============================================================================
// MAIN DETAIL COMPONENT
// ============================================================================
export default function FundingResearchDetail({ ein, onClose, onNavigateToOrg }) {
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)

  useEffect(() => {
    loadOrgDetail()
  }, [ein])

  async function loadOrgDetail() {
    setLoading(true)
    try {
      const res = await apiClient.getNonprofitDetail(ein)
      setData(res.data)
    } catch (err) {
      toast.error('Failed to load organization details')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-8">
        <div className="flex items-center justify-center gap-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <p className="text-gray-500">Loading organization data...</p>
        </div>
      </div>
    )
  }

  if (!data?.org) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <p className="text-gray-500">Organization not found.</p>
        <button onClick={onClose} className="mt-3 text-sm text-blue-600 hover:underline">
          Back to search
        </button>
      </div>
    )
  }

  const { org, filings = [], personnel = [], awards = [], peers = [] } = data

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-5 text-white">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-bold truncate">{org.name_legal}</h2>
            <div className="flex items-center gap-3 mt-1.5 text-blue-100 text-sm">
              <span>EIN {org.ein}</span>
              {org.city && <span>&bull; {org.city}, {org.state}</span>}
              {org.ntee_code && <span>&bull; NTEE {org.ntee_code}</span>}
            </div>
            {org.revenue_latest != null && (
              <p className="mt-2 text-2xl font-bold text-white/90">
                {formatCurrency(org.revenue_latest)}
                <span className="text-sm font-normal text-blue-200 ml-2">latest revenue</span>
              </p>
            )}
          </div>
          <button onClick={onClose}
                  className="p-1.5 rounded-lg hover:bg-white/20 transition-colors shrink-0 ml-4">
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 px-6">
        <div className="flex gap-1 -mb-px overflow-x-auto">
          {TABS.map(tab => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            const count = tab.id === 'financials' ? filings.length
              : tab.id === 'awards' ? awards.length
              : tab.id === 'people' ? personnel.length
              : tab.id === 'peers' ? peers.length
              : null
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap
                  ${isActive
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
                {count != null && count > 0 && (
                  <span className={`text-xs px-1.5 py-0.5 rounded-full ${isActive ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'}`}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'overview' && <OverviewTab org={org} />}
        {activeTab === 'financials' && <FinancialsTab filings={filings} />}
        {activeTab === 'awards' && <AwardsTab awards={awards} />}
        {activeTab === 'people' && <PeopleTab personnel={personnel} />}
        {activeTab === 'peers' && (
          <PeersTab
            peers={peers}
            onSelectOrg={(newEin) => onNavigateToOrg?.(newEin)}
          />
        )}
      </div>
    </div>
  )
}
