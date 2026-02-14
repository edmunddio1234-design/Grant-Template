import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PieChart, Pie, BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import { AlertTriangle, TrendingDown, Zap, FileSearch, ArrowRight, RefreshCw, Loader2 } from 'lucide-react'
import RiskBadge from '../components/common/RiskBadge'
import { apiClient } from '../api/client'

function clsx(...classes) {
  return classes.filter(Boolean).join(' ')
}

export default function GapRiskDashboard() {
  const navigate = useNavigate()
  const [rfpList, setRfpList] = useState([])
  const [selectedRFP, setSelectedRFP] = useState(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [hasData, setHasData] = useState(false)

  // Real analysis data from API
  const [overallScore, setOverallScore] = useState(0)
  const [riskDistribution, setRiskDistribution] = useState([])
  const [categoryScores, setCategoryScores] = useState([])
  const [timelineData, setTimelineData] = useState([])
  const [gaps, setGaps] = useState([])
  const [recommendations, setRecommendations] = useState([])

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
        }
      } catch (err) {
        console.log('RFP list unavailable:', err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchRFPs()
  }, [])

  // Fetch gap/risk data from API when RFP changes
  useEffect(() => {
    if (!selectedRFP) {
      setLoading(false)
      return
    }

    async function fetchGapRisk() {
      setAnalyzing(true)
      setHasData(false)

      try {
        const [gapRes, riskRes, recRes] = await Promise.all([
          apiClient.getGapAnalysis(selectedRFP).catch(() => null),
          apiClient.getRiskDistribution(selectedRFP).catch(() => null),
          apiClient.getRecommendations(selectedRFP).catch(() => null)
        ])

        let foundData = false

        if (gapRes?.data) {
          const score = gapRes.data.overall_score || gapRes.data.overallScore
          if (score !== undefined && score !== null) {
            setOverallScore(score)
            foundData = true
          }
          if (Array.isArray(gapRes.data.gaps) && gapRes.data.gaps.length > 0) {
            setGaps(gapRes.data.gaps)
            foundData = true
          } else {
            setGaps([])
          }
          if (Array.isArray(gapRes.data.category_scores) && gapRes.data.category_scores.length > 0) {
            setCategoryScores(gapRes.data.category_scores)
          } else {
            setCategoryScores([])
          }
          if (Array.isArray(gapRes.data.timeline) && gapRes.data.timeline.length > 0) {
            setTimelineData(gapRes.data.timeline)
          } else {
            setTimelineData([])
          }
        }

        if (riskRes?.data) {
          const dist = riskRes.data.distribution || riskRes.data
          if (Array.isArray(dist) && dist.length > 0) {
            setRiskDistribution(dist)
            foundData = true
          } else {
            setRiskDistribution([])
          }
        }

        if (recRes?.data) {
          const recs = Array.isArray(recRes.data) ? recRes.data : recRes.data.recommendations
          if (Array.isArray(recs) && recs.length > 0) {
            setRecommendations(recs)
            foundData = true
          } else {
            setRecommendations([])
          }
        }

        setHasData(foundData)
      } catch (err) {
        console.log('Gap/Risk API unavailable:', err.message)
        setHasData(false)
      } finally {
        setAnalyzing(false)
      }
    }

    fetchGapRisk()
  }, [selectedRFP])

  // Loading state
  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div>
          <h2 className="section-title">Gap & Risk Dashboard</h2>
          <p className="text-gray-600 mt-2">Identify and prioritize gaps and risks in grant applications</p>
        </div>
        <div className="card p-12 text-center">
          <Loader2 size={32} className="mx-auto text-brand-primary animate-spin mb-3" />
          <p className="text-sm text-gray-500">Loading RFPs...</p>
        </div>
      </div>
    )
  }

  // No RFPs uploaded yet
  if (rfpList.length === 0) {
    return (
      <div className="p-6 space-y-6">
        <div>
          <h2 className="section-title">Gap & Risk Dashboard</h2>
          <p className="text-gray-600 mt-2">Identify and prioritize gaps and risks in grant applications</p>
        </div>
        <div className="card p-12 text-center">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center mb-4">
            <FileSearch size={32} className="text-blue-400" />
          </div>
          <h3 className="text-lg font-bold text-gray-800 mb-2">No RFPs Found</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto mb-6">
            Upload an RFP first, then run a crosswalk analysis. The gap & risk dashboard will show you exactly where your proposal is strong and where it needs work.
          </p>
          <button
            onClick={() => navigate('/rfp')}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-brand-primary to-blue-700 text-white rounded-xl text-sm font-semibold hover:opacity-90 transition-all shadow-md"
          >
            Upload an RFP <ArrowRight size={16} />
          </button>
        </div>
      </div>
    )
  }

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

      {/* Analyzing state */}
      {analyzing && (
        <div className="card p-12 text-center">
          <Loader2 size={32} className="mx-auto text-brand-primary animate-spin mb-3" />
          <p className="text-sm text-gray-500 font-medium">Analyzing gaps and risks...</p>
        </div>
      )}

      {/* No analysis data — show helpful empty state */}
      {!analyzing && !hasData && (
        <div className="card overflow-hidden">
          <div className="relative p-10 text-center">
            {/* Subtle background decoration */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-400 via-orange-400 to-red-400" />
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-amber-50 opacity-50" />
              <div className="absolute -bottom-10 -left-10 w-32 h-32 rounded-full bg-orange-50 opacity-50" />
            </div>

            <div className="relative z-10">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center mb-4 border border-amber-200">
                <AlertTriangle size={32} className="text-amber-500" />
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-2">No Gap Analysis Available</h3>
              <p className="text-sm text-gray-500 max-w-lg mx-auto mb-6">
                This RFP hasn't been analyzed yet. Run a crosswalk analysis first to map RFP requirements against your boilerplate content, then the gap analysis will identify weaknesses and generate actionable recommendations.
              </p>
              <div className="flex items-center justify-center gap-3">
                <button
                  onClick={() => navigate('/crosswalk')}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-brand-primary to-blue-700 text-white rounded-xl text-sm font-semibold hover:opacity-90 transition-all shadow-md"
                >
                  Run Crosswalk Analysis <ArrowRight size={16} />
                </button>
                <button
                  onClick={() => {
                    setAnalyzing(true)
                    setHasData(false)
                    // Re-trigger fetch
                    const rfpId = selectedRFP
                    setSelectedRFP(null)
                    setTimeout(() => setSelectedRFP(rfpId), 100)
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-50 transition-all"
                >
                  <RefreshCw size={14} /> Retry
                </button>
              </div>

              {/* How it works */}
              <div className="mt-8 pt-6 border-t border-gray-100">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">How Gap Analysis Works</p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto">
                  <div className="text-center p-3">
                    <div className="w-8 h-8 mx-auto rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-bold mb-2">1</div>
                    <p className="text-xs text-gray-600">Upload & parse your RFP to extract requirements</p>
                  </div>
                  <div className="text-center p-3">
                    <div className="w-8 h-8 mx-auto rounded-full bg-violet-100 text-violet-600 flex items-center justify-center text-sm font-bold mb-2">2</div>
                    <p className="text-xs text-gray-600">Run crosswalk to map requirements to boilerplate</p>
                  </div>
                  <div className="text-center p-3">
                    <div className="w-8 h-8 mx-auto rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-sm font-bold mb-2">3</div>
                    <p className="text-xs text-gray-600">Gap analysis identifies weaknesses & generates a plan</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Real data display — only renders when we have actual API data */}
      {!analyzing && hasData && (
        <>
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

          {/* Charts — only show when we have chart data */}
          {(riskDistribution.length > 0 || categoryScores.length > 0) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {riskDistribution.length > 0 && (
                <div className="card">
                  <div className="p-6 border-b border-gray-200">
                    <h3 className="subsection-title">Risk Distribution</h3>
                    <p className="text-sm text-gray-600 mt-1">By severity level</p>
                  </div>
                  <div className="p-6">
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={riskDistribution}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, value }) => `${name}: ${value}`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {riskDistribution.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill || entry.color || '#64748B'} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {categoryScores.length > 0 && (
                <div className="card">
                  <div className="p-6 border-b border-gray-200">
                    <h3 className="subsection-title">Category Scores</h3>
                    <p className="text-sm text-gray-600 mt-1">Strength by category</p>
                  </div>
                  <div className="p-6">
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={categoryScores}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="category" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="score" fill="#0F2C5C" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Timeline — only if data exists */}
          {timelineData.length > 0 && (
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
          )}

          {/* Gap Findings — only if data exists */}
          {gaps.length > 0 && (
            <div className="space-y-4">
              <h3 className="subsection-title">Gap Findings</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {gaps.map((gap, idx) => (
                  <div key={gap.id || idx} className="card">
                    <div className="p-6">
                      <div className="flex items-start gap-3 mb-4">
                        <AlertTriangle size={20} className={clsx(
                          'flex-shrink-0 mt-1',
                          gap.severity === 'red' && 'text-red-600',
                          gap.severity === 'yellow' && 'text-amber-600',
                          gap.severity === 'green' && 'text-green-600'
                        )} />
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900">{gap.title}</h4>
                          <RiskBadge level={gap.severity} showIcon={false} />
                        </div>
                      </div>

                      <p className="text-sm text-gray-700 mb-3">{gap.description}</p>

                      {gap.impact && (
                        <div className="p-3 bg-gray-50 rounded-lg mb-3">
                          <p className="text-xs text-gray-600 mb-1">Impact</p>
                          <p className="text-sm font-medium text-gray-900">{gap.impact}</p>
                        </div>
                      )}

                      {gap.recommendation && (
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Recommendation</p>
                          <p className="text-sm text-gray-900">{gap.recommendation}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations — only if data exists */}
          {recommendations.length > 0 && (
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
                  {recommendations.map((rec, idx) => (
                    <div key={rec.priority || idx} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-brand-primary transition-colors">
                      <div className="flex-shrink-0">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-primary text-white font-bold text-sm">
                          {rec.priority || idx + 1}
                        </div>
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{rec.action}</p>
                        <div className="flex gap-4 mt-2 text-sm text-gray-600">
                          {rec.timeline && <span>Timeline: {rec.timeline}</span>}
                          {rec.timeline && rec.impact && <span>•</span>}
                          {rec.impact && <span>Impact: +{rec.impact}</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
