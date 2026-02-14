import { useState, useCallback } from 'react'
import {
  Search, Building2, DollarSign, MapPin, Filter,
  Loader2, ArrowLeft, X, Hash, Globe, ChevronRight,
  SearchCheck, Sparkles, TrendingUp
} from 'lucide-react'
import { apiClient } from '../api/client'
import FundingResearchDetail from '../components/FundingResearchDetail'
import toast from 'react-hot-toast'

const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
  'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
  'VA','WA','WV','WI','WY','DC','PR','VI','GU','AS','MP'
]

function formatCurrency(val) {
  if (val == null) return '—'
  return '$' + Number(val).toLocaleString(undefined, { maximumFractionDigits: 0 })
}

// ============================================================================
// SEARCH FORM
// ============================================================================
function SearchForm({ onSearch, loading }) {
  const [query, setQuery] = useState('')
  const [state, setState] = useState('')
  const [city, setCity] = useState('')
  const [nteeCode, setNteeCode] = useState('')
  const [minRevenue, setMinRevenue] = useState('')
  const [maxRevenue, setMaxRevenue] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  function handleSubmit(e) {
    e.preventDefault()
    const params = {}
    if (query.trim()) params.query = query.trim()
    if (state) params.state = state
    if (city.trim()) params.city = city.trim()
    if (nteeCode.trim()) params.ntee_code = nteeCode.trim()
    if (minRevenue) params.min_revenue = Number(minRevenue)
    if (maxRevenue) params.max_revenue = Number(maxRevenue)
    if (Object.keys(params).length === 0) {
      toast.error('Enter a search term or filter')
      return
    }
    onSearch(params)
  }

  function handleClear() {
    setQuery('')
    setState('')
    setCity('')
    setNteeCode('')
    setMinRevenue('')
    setMaxRevenue('')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Main search row */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by organization name or EIN..."
            className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
        </div>
        <button
          type="button"
          onClick={() => setShowFilters(!showFilters)}
          className={`px-4 py-3 rounded-lg border text-sm font-medium flex items-center gap-2 transition-colors
            ${showFilters ? 'bg-blue-50 border-blue-300 text-blue-700' : 'border-gray-300 text-gray-600 hover:bg-gray-50'}`}
        >
          <Filter className="w-4 h-4" />
          Filters
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          Search
        </button>
      </div>

      {/* Advanced filters */}
      {showFilters && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">State</label>
            <select
              value={state}
              onChange={(e) => setState(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Any state</option>
              {US_STATES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">City</label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="e.g. New York"
              className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">NTEE Code</label>
            <input
              type="text"
              value={nteeCode}
              onChange={(e) => setNteeCode(e.target.value)}
              placeholder="e.g. B, P20"
              className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Min Revenue</label>
            <input
              type="number"
              value={minRevenue}
              onChange={(e) => setMinRevenue(e.target.value)}
              placeholder="$0"
              className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Max Revenue</label>
            <input
              type="number"
              value={maxRevenue}
              onChange={(e) => setMaxRevenue(e.target.value)}
              placeholder="No limit"
              className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="col-span-2 md:col-span-5 flex justify-end">
            <button type="button" onClick={handleClear}
                    className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1">
              <X className="w-3 h-3" /> Clear all filters
            </button>
          </div>
        </div>
      )}
    </form>
  )
}

// ============================================================================
// RESULT CARD
// ============================================================================
function OrgCard({ org, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-5 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all group"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
            {org.name_legal}
          </h3>
          <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Hash className="w-3 h-3" />
              {org.ein}
            </span>
            {org.city && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {org.city}, {org.state}
              </span>
            )}
            {org.ntee_code && (
              <span className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-xs font-medium">
                NTEE {org.ntee_code}
              </span>
            )}
          </div>
          {org.mission && (
            <p className="text-sm text-gray-500 mt-2 line-clamp-2">
              {org.mission}
            </p>
          )}
        </div>
        <div className="text-right ml-4 shrink-0">
          {org.revenue_latest != null && (
            <p className="text-lg font-bold text-green-700">
              {formatCurrency(org.revenue_latest)}
            </p>
          )}
          <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-blue-400 mt-1 ml-auto transition-colors" />
        </div>
      </div>
    </button>
  )
}

// ============================================================================
// WELCOME / EMPTY STATE
// ============================================================================
function WelcomeState() {
  return (
    <div className="text-center py-16">
      <div className="relative inline-block mb-6">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
          <SearchCheck className="w-10 h-10 text-white" />
        </div>
        <div className="absolute -top-1 -right-1 w-6 h-6 bg-amber-400 rounded-full flex items-center justify-center">
          <Sparkles className="w-3.5 h-3.5 text-amber-900" />
        </div>
      </div>
      <h3 className="text-xl font-bold text-gray-800 mb-2">Funding Research Intelligence</h3>
      <p className="text-gray-500 max-w-lg mx-auto mb-8">
        Search millions of nonprofits by name, EIN, state, or NTEE code. View 990 filings,
        federal awards, officer compensation, and peer comparisons — all in one place.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto">
        <FeatureCard
          icon={Building2}
          title="Org Profiles"
          desc="Mission, leadership, NTEE classification, and contact details"
          color="blue"
        />
        <FeatureCard
          icon={DollarSign}
          title="Financials & Awards"
          desc="990 filing history and federal grant awards from USAspending"
          color="green"
        />
        <FeatureCard
          icon={TrendingUp}
          title="Peer Benchmarks"
          desc="Compare against similar orgs by type, state, and revenue"
          color="purple"
        />
      </div>
    </div>
  )
}

function FeatureCard({ icon: Icon, title, desc, color }) {
  const colorMap = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
  }
  return (
    <div className="p-4 rounded-xl border border-gray-100 bg-white">
      <div className={`w-10 h-10 rounded-lg ${colorMap[color]} flex items-center justify-center mb-3`}>
        <Icon className="w-5 h-5" />
      </div>
      <h4 className="font-medium text-gray-800 text-sm">{title}</h4>
      <p className="text-xs text-gray-500 mt-1">{desc}</p>
    </div>
  )
}

// ============================================================================
// MAIN PAGE
// ============================================================================
export default function FundingResearch() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedEin, setSelectedEin] = useState(null)

  const handleSearch = useCallback(async (params) => {
    setLoading(true)
    setSelectedEin(null)
    try {
      const res = await apiClient.searchNonprofits(params)
      setResults(res.data)
    } catch (err) {
      toast.error('Search failed. Please try again.')
      setResults(null)
    } finally {
      setLoading(false)
    }
  }, [])

  // Detail view
  if (selectedEin) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => setSelectedEin(null)}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to search results
        </button>
        <FundingResearchDetail
          ein={selectedEin}
          onClose={() => setSelectedEin(null)}
          onNavigateToOrg={(ein) => setSelectedEin(ein)}
        />
      </div>
    )
  }

  // Search view
  const orgs = results?.orgs || []

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Funding Research</h1>
        <p className="text-sm text-gray-500 mt-1">
          Search nonprofit organizations, view financials, federal awards, and peer comparisons
        </p>
      </div>

      {/* Search Form */}
      <SearchForm onSearch={handleSearch} loading={loading} />

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <p className="ml-3 text-gray-500">Searching nonprofits...</p>
        </div>
      ) : results === null ? (
        <WelcomeState />
      ) : orgs.length === 0 ? (
        <div className="text-center py-16">
          <Search className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-600">No organizations found</h3>
          <p className="text-sm text-gray-400 mt-1">Try a different search term or adjust your filters</p>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-gray-500 font-medium">{orgs.length} organizations found</p>
          <div className="grid gap-3">
            {orgs.map(org => (
              <OrgCard
                key={org.ein}
                org={org}
                onClick={() => setSelectedEin(org.ein)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
