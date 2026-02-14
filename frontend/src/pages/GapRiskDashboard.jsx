import { useState, useEffect } from 'react'
import { PieChart, Pie, BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import { AlertTriangle, TrendingDown, Zap } from 'lucide-react'
import RiskBadge from '../components/common/RiskBadge'
import { apiClient } from '../api/client'

const mockRFPs = [
  { id: 1, name: 'Community Foundation Grant 2024' },
  { id: 2, name: 'Department of Family Services RFP' },
  { id: 3, name: 'Local Nonprofit Partnership Grant' }
]

const riskDistributionData = [
  { name: 'Green (Low Risk)', value: 12, fill: '#22C55E' },
  { name: 'Yellow (Medium Risk)', value: 6, fill: '#F59E0B' },
  { name: 'Red (High Risk)', value: 2, fill: '#EF4444' }
]

const categoryScoresData = [
  { category: 'Metrics', score: 78 },
  { category: 'Alignment', score: 82 },
  { category: 'Data', score: 65 },
  { category: 'Partnerships', score: 55 },
  { category: 'Match', score: 88 },
  { category: 'Evaluation', score: 72 }
]

const timelineData = [
  { month: 'Jan', score: 68 },
  { month: 'Feb', score: 72 },
  { month: 'Mar', score: 75 }
]

const gaps = [
  {
    id: 1,
    title: 'Missing Community Partnerships Section',
    severity: 'red',
    description: 'RFP requires evidence of established partnerships with community organizations',
    impact: 'Critical - 20% score reduction',
    recommendation: 'Develop partnership narrative with letters of support'
  },
  {
    id: 2,
    title: 'Weak Evaluation Methodology',
    severity: 'yellow',
    description: 'Current evaluation framework lacks quantitative metrics',
    impact: 'High - 15% score reduction',
    recommendation: 'Add pre/post assessment data and outcome metrics'
  },
  {
    id: 3,
    title: 'Insufficient Sustainability Plan',
    severity: 'red',
    description: 'No detailed plan for program continuation beyond grant period',
    impact: 'Critical - 18% score reduction',
    recommendation: 'Create sustainability strategy with revenue diversification plan'
  },
  {
    id: 4,
    title: 'Limited Staff Qualifications Documentation',
    severity: 'yellow',
    description: 'Missing detailed staff bios and relevant experience',
    impact: 'Medium - 10% score reduction',
    recommendation: 'Add staff biographical information and certifications'
  },
  {
    id: 5,
    title: 'Outdated Program Data',
    severity: 'yellow',
    description: 'Outcome data is from 2022, RFP requests current year data',
    impact: 'Medium - 12% score reduction',
    recommendation: 'Update evaluation data with 2024 participant outcomes'
  }
]

const recommendations = [
  {
    priority: 1,
    action: 'Establish formal community partnerships',
    timeline: '2 weeks',
    impact: '20%'
  },
  {
    priority: 2,
    action: 'Develop comprehensive evaluation plan with metrics',
    timeline: '3 weeks',
    impact: '15%'
  },
  {
    priority: 3,
    action: 'Create detailed sustainability strategy',
    timeline: '2 weeks',
    impact: '18%'
  },
  {
    priority: 4,
    action: 'Compile staff qualifications and certifications',
    timeline: '1 week',
    impact: '10%'
  },
  {
    priority: 5,
    action: 'Update all outcome data to current year',
    timeline: '1 week',
    impact: '12%'
  }
]

export default function GapRiskDashboard() {
  const [rfpList, setRfpList] = useState(mockRFPs)
  const [selectedRFP, setSelectedRFP] = useState(null)
  const [overallScore, setOverallScore] = useState(74)
  const [apiGaps, setApiGaps] = useState(null)
  const [apiRecommendations, setApiRecommendations] = useState(null)

  // Fetch real RFPs on mount
  useEffect(() => {
    async function fetchRFPs() {
      try {
        const res = await apiClient.listRFPs({ limit: 50 })
        const data = res.data
        const items = data.items || data.results || data
        if (Array.isArray(items) && items.length > 0) {
          const mapped = items.map(r => ({ id: r.id, name: r.title || r.name }))
          setRfpList(mapped)
          setSelectedRFP(mapped[0].id)
        } else {
          setSelectedRFP(mockRFPs[0].id)
        }
      } catch (err) {
        console.log('RFP list unavailable, using mock data:', err.message)
        setSelectedRFP(mockRFPs[0].id)
      }
    }
    fetchRFPs()
  }, [])

  // Fetch gap/risk data from API when RFP changes
  useEffect(() => {
    if (!selectedRFP) return
    async function fetchGapRisk() {
      try {
        const [gapRes, riskRes, recRes] = await Promise.all([
          apiClient.getGapAnalysis(selectedRFP),
          apiClient.getRiskDistribution(selectedRFP),
          apiClient.getRecommendations(selectedRFP)
        ])
        if (gapRes.data) {
          setOverallScore(gapRes.data.overall_score || gapRes.data.overallScore || 74)
          if (Array.isArray(gapRes.data.gaps)) setApiGaps(gapRes.data.gaps)
        }
        if (Array.isArray(recRes.data)) setApiRecommendations(recRes.data)
      } catch (err) {
        console.log('Gap/Risk API unavailable, using mock data:', err.message)
      }
    }
    fetchGapRisk()
  }, [selectedRFP])

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="section-title">Gap & Risk Dashboard</h2>
        <p className="text-gray-600 mt-2">Identify and prioritize gaps and risks in grant applications</p>
      </div>

      {/* RFP Selector */}
      <div className="card">
        <div className="p-6">
          <label className="block text-sm font-medium text-gray-900 mb-3">Select RFP</label>
          <select
            value={selectedRFP || ''}
            onChange={(e) => setSelectedRFP(e.target.value)}
            className="input-field max-w-md"
          >
            {rfpList.map((rfp) => (
              <option key={rfp.id} value={rfp.id}>{rfp.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Overall Risk Score */}
      <div className="card">
        <div className="p-8">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-2">Overall Risk Score</p>
              <div className="flex items-baseline gap-4">
                <p className="text-6xl font-bold text-brand-primary">{overallScore}</p>
                <p className="text-2xl text-gray-500">/100</p>
              </div>
              <p className="text-sm text-gray-600 mt-3">Lower score indicates higher risk</p>
            </div>

            <div className="relative w-32 h-32">
              <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                <circle cx="50" cy="50" r="45" fill="none" stroke="#e5e7eb" strokeWidth="8" />
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="#0F2C5C"
                  strokeWidth="8"
                  strokeDasharray={`${(overallScore / 100) * 282.7} 282.7`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-xl font-bold text-gray-900">{overallScore}%</p>
                  <p className="text-xs text-gray-600">Readiness</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <h3 className="subsection-title">Risk Distribution</h3>
            <p className="text-sm text-gray-600 mt-1">By severity level</p>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={riskDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {riskDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Scores */}
        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <h3 className="subsection-title">Category Scores</h3>
            <p className="text-sm text-gray-600 mt-1">Strength by category</p>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryScoresData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="score" fill="#0F2C5C" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="card">
        <div className="p-6 border-b border-gray-200">
          <h3 className="subsection-title">Score Improvement Timeline</h3>
          <p className="text-sm text-gray-600 mt-1">Progress over time</p>
        </div>
        <div className="p-6">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="score" stroke="#0F2C5C" strokeWidth={2} name="Score" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Gaps Section */}
      <div className="space-y-4">
        <h3 className="subsection-title">Gap Findings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {gaps.map((gap) => (
            <div key={gap.id} className="card">
              <div className="p-6">
                <div className="flex items-start gap-3 mb-4">
                  <AlertTriangle size={20} className={clsx(
                    'flex-shrink-0 mt-1',
                    gap.severity === 'red' && 'text-red-600',
                    gap.severity === 'yellow' && 'text-amber-600'
                  )} />
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900">{gap.title}</h4>
                    <RiskBadge level={gap.severity} showIcon={false} />
                  </div>
                </div>

                <p className="text-sm text-gray-700 mb-3">{gap.description}</p>

                <div className="p-3 bg-gray-50 rounded-lg mb-3">
                  <p className="text-xs text-gray-600 mb-1">Impact</p>
                  <p className="text-sm font-medium text-gray-900">{gap.impact}</p>
                </div>

                <div>
                  <p className="text-xs text-gray-600 mb-1">Recommendation</p>
                  <p className="text-sm text-gray-900">{gap.recommendation}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations Section */}
      <div className="card">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Zap size={20} className="text-brand-amber" />
            <h3 className="subsection-title">Prioritized Action Plan</h3>
          </div>
          <p className="text-sm text-gray-600 mt-1">Recommended steps to maximize grant competitiveness</p>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            {recommendations.map((rec) => (
              <div key={rec.priority} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-brand-primary transition-colors">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-primary text-white font-bold text-sm">
                    {rec.priority}
                  </div>
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{rec.action}</p>
                  <div className="flex gap-4 mt-2 text-sm text-gray-600">
                    <span>Timeline: {rec.timeline}</span>
                    <span>•</span>
                    <span>Impact: +{rec.impact}</span>
                  </div>
                </div>
                <button className="btn-secondary btn-sm flex-shrink-0">
                  Assign
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Missing Items */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <h4 className="font-semibold text-gray-900">Missing Metrics</h4>
          </div>
          <div className="p-6 space-y-3">
            <div className="flex items-center gap-2 p-2 bg-red-50 rounded text-red-800 text-sm">
              <span className="text-lg">⊘</span>
              Participant satisfaction scores
            </div>
            <div className="flex items-center gap-2 p-2 bg-red-50 rounded text-red-800 text-sm">
              <span className="text-lg">⊘</span>
              Long-term outcome tracking
            </div>
            <div className="flex items-center gap-2 p-2 bg-red-50 rounded text-red-800 text-sm">
              <span className="text-lg">⊘</span>
              Cost per participant analysis
            </div>
          </div>
        </div>

        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <h4 className="font-semibold text-gray-900">Missing Partnerships</h4>
          </div>
          <div className="p-6 space-y-3">
            <div className="flex items-center gap-2 p-2 bg-red-50 rounded text-red-800 text-sm">
              <span className="text-lg">⊘</span>
              School district collaboration
            </div>
            <div className="flex items-center gap-2 p-2 bg-red-50 rounded text-red-800 text-sm">
              <span className="text-lg">⊘</span>
              Health services partnerships
            </div>
            <div className="flex items-center gap-2 p-2 bg-red-50 rounded text-red-800 text-sm">
              <span className="text-lg">⊘</span>
              Government agency coordination
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function clsx(...classes) {
  return classes.filter(Boolean).join(' ')
}
