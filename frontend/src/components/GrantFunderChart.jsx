import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Award, Clock, XCircle, ChevronDown, ChevronUp, BarChart3, TrendingUp, Zap, Loader2, Upload, FileText, GitCompare, PenTool, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react'
import { apiClient } from '../api/client'

// Color palette for funder categories
const CATEGORY_STYLES = {
  federal:    { gradient: 'from-blue-500 to-indigo-600', color: '#3B82F6', accent: '#818CF8' },
  state:      { gradient: 'from-violet-500 to-purple-600', color: '#8B5CF6', accent: '#A78BFA' },
  government: { gradient: 'from-blue-500 to-indigo-600', color: '#3B82F6', accent: '#818CF8' },
  corporate:  { gradient: 'from-emerald-400 to-teal-600', color: '#10B981', accent: '#14B8A6' },
  foundation: { gradient: 'from-amber-400 to-orange-500', color: '#F59E0B', accent: '#F97316' },
  community:  { gradient: 'from-pink-500 to-rose-600', color: '#EC4899', accent: '#F43F5E' },
  nonprofit:  { gradient: 'from-cyan-400 to-blue-500', color: '#06B6D4', accent: '#3B82F6' },
  other:      { gradient: 'from-gray-400 to-slate-500', color: '#64748B', accent: '#94A3B8' },
}
const STYLE_LIST = Object.values(CATEGORY_STYLES)

function getStyleForCategory(cat, idx) {
  const key = (cat || 'other').toLowerCase()
  return CATEGORY_STYLES[key] || STYLE_LIST[idx % STYLE_LIST.length]
}

function enrichFunders(raw) {
  return raw.map((d, i) => ({
    ...d,
    ...getStyleForCategory(d.category, i),
  }))
}

function fmt(val) {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}

function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3) }

// =============================================
// WELCOME HERO — shown when no funder data yet
// =============================================
const WORKFLOW_STEPS = [
  {
    icon: Upload,
    title: 'Upload RFP',
    desc: 'Drop in any grant RFP document and the AI parser extracts every requirement automatically.',
    color: 'from-blue-500 to-indigo-600',
    bgLight: 'bg-blue-50',
    textColor: 'text-blue-600',
    borderColor: 'border-blue-200',
    route: '/rfp',
  },
  {
    icon: FileText,
    title: 'Build Boilerplate',
    desc: 'Store your org\'s reusable narratives, data points, and evidence-based language.',
    color: 'from-emerald-500 to-teal-600',
    bgLight: 'bg-emerald-50',
    textColor: 'text-emerald-600',
    borderColor: 'border-emerald-200',
    route: '/boilerplate',
  },
  {
    icon: GitCompare,
    title: 'Run Crosswalk',
    desc: 'AI maps every RFP requirement against your boilerplate — gaps and strengths surfaced instantly.',
    color: 'from-violet-500 to-purple-600',
    bgLight: 'bg-violet-50',
    textColor: 'text-violet-600',
    borderColor: 'border-violet-200',
    route: '/crosswalk',
  },
  {
    icon: PenTool,
    title: 'Generate Draft',
    desc: 'One click creates a full grant narrative draft, section by section, ready for review.',
    color: 'from-amber-500 to-orange-600',
    bgLight: 'bg-amber-50',
    textColor: 'text-amber-600',
    borderColor: 'border-amber-200',
    route: '/ai-draft',
  },
]

function WelcomeHero() {
  const navigate = useNavigate()
  const [activeStep, setActiveStep] = useState(0)
  const [mounted, setMounted] = useState(false)
  const [particles, setParticles] = useState([])

  useEffect(() => {
    setMounted(true)
    // Generate floating particles once
    const pts = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: 2 + Math.random() * 4,
      duration: 8 + Math.random() * 12,
      delay: Math.random() * 5,
      opacity: 0.1 + Math.random() * 0.15,
    }))
    setParticles(pts)
  }, [])

  // Auto-rotate through steps
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep(s => (s + 1) % WORKFLOW_STEPS.length)
    }, 4000)
    return () => clearInterval(interval)
  }, [])

  const step = WORKFLOW_STEPS[activeStep]
  const StepIcon = step.icon

  return (
    <>
      <style>{`
        @keyframes floatParticle {
          0%, 100% { transform: translateY(0px) translateX(0px); }
          25% { transform: translateY(-15px) translateX(8px); }
          50% { transform: translateY(-5px) translateX(-6px); }
          75% { transform: translateY(-20px) translateX(4px); }
        }
        @keyframes pulseGlow {
          0%, 100% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.15); }
          50% { box-shadow: 0 0 40px rgba(99, 102, 241, 0.3); }
        }
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes fadeInScale {
          from { opacity: 0; transform: scale(0.9); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes gradientShift {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        .hero-card-enter { animation: fadeInScale 0.4s ease-out forwards; }
        .hero-slide-in { animation: slideInRight 0.5s ease-out forwards; }
        .gradient-animate {
          background-size: 200% 200%;
          animation: gradientShift 6s ease infinite;
        }
      `}</style>

      <div className={`relative w-full overflow-hidden rounded-2xl border border-gray-100 shadow-sm bg-white transition-all duration-700 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
        {/* Animated gradient top bar */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-500 via-purple-500 via-pink-500 to-blue-500 rounded-t-2xl gradient-animate" />

        {/* Floating particles */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {particles.map(p => (
            <div
              key={p.id}
              className="absolute rounded-full bg-indigo-400"
              style={{
                left: `${p.x}%`,
                top: `${p.y}%`,
                width: p.size,
                height: p.size,
                opacity: p.opacity,
                animation: `floatParticle ${p.duration}s ease-in-out ${p.delay}s infinite`,
              }}
            />
          ))}
        </div>

        <div className="relative z-10 p-6 md:p-8">
          {/* Header row */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <div className="flex items-center gap-2.5 mb-2">
                <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg" style={{ animation: 'pulseGlow 3s ease-in-out infinite' }}>
                  <Sparkles size={20} className="text-white" />
                </div>
                <div>
                  <h2 className="text-xl md:text-2xl font-extrabold text-gray-900 tracking-tight">
                    Grant Alignment Engine
                  </h2>
                  <p className="text-sm text-gray-400 font-medium">Your AI-powered grant writing workflow</p>
                </div>
              </div>
            </div>
            <button
              onClick={() => navigate('/rfp')}
              className="hidden sm:flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl text-sm font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5"
            >
              Get Started <ArrowRight size={16} />
            </button>
          </div>

          {/* Workflow Steps — interactive timeline */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* Left: Step selector */}
            <div className="space-y-2">
              {WORKFLOW_STEPS.map((s, i) => {
                const Icon = s.icon
                const isActive = i === activeStep
                return (
                  <button
                    key={i}
                    onClick={() => setActiveStep(i)}
                    className={`w-full flex items-center gap-3 p-3 rounded-xl text-left transition-all duration-300 border ${
                      isActive
                        ? `${s.bgLight} ${s.borderColor} shadow-sm`
                        : 'border-transparent hover:bg-gray-50'
                    }`}
                  >
                    <div className={`p-2 rounded-lg transition-all duration-300 ${
                      isActive
                        ? `bg-gradient-to-br ${s.color} text-white shadow-md`
                        : 'bg-gray-100 text-gray-400'
                    }`}>
                      <Icon size={18} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-bold ${isActive ? s.textColor : 'text-gray-300'}`}>
                          STEP {i + 1}
                        </span>
                        {i === 0 && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-600 font-semibold">
                            START HERE
                          </span>
                        )}
                      </div>
                      <p className={`text-sm font-semibold truncate ${isActive ? 'text-gray-900' : 'text-gray-500'}`}>
                        {s.title}
                      </p>
                    </div>
                    <ArrowRight size={14} className={`transition-all duration-300 ${isActive ? `${s.textColor} translate-x-0 opacity-100` : 'opacity-0 -translate-x-2'}`} />
                  </button>
                )
              })}
            </div>

            {/* Right: Active step detail card */}
            <div className="flex items-center" key={activeStep}>
              <div className={`hero-card-enter w-full p-5 rounded-xl border ${step.borderColor} ${step.bgLight}`}>
                <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border ${step.borderColor} mb-3`}>
                  <StepIcon size={14} className={step.textColor} />
                  <span className={`text-xs font-bold ${step.textColor}`}>{step.title}</span>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed mb-4">
                  {step.desc}
                </p>
                <button
                  onClick={() => navigate(step.route)}
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r ${step.color} text-white text-sm font-semibold hover:opacity-90 transition-all shadow-sm hover:shadow-md`}
                >
                  Go to {step.title} <ArrowRight size={14} />
                </button>
              </div>
            </div>
          </div>

          {/* Progress dots */}
          <div className="flex items-center justify-center gap-2 mt-2">
            {WORKFLOW_STEPS.map((s, i) => (
              <button
                key={i}
                onClick={() => setActiveStep(i)}
                className={`transition-all duration-300 rounded-full ${
                  i === activeStep
                    ? `w-8 h-2 bg-gradient-to-r ${s.color}`
                    : 'w-2 h-2 bg-gray-200 hover:bg-gray-300'
                }`}
              />
            ))}
          </div>

          {/* Mobile CTA */}
          <button
            onClick={() => navigate('/rfp')}
            className="sm:hidden w-full mt-4 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl text-sm font-semibold"
          >
            Get Started <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </>
  )
}

// Animated gradient blobs floating in background
function GradientBlobs({ data }) {
  const blobs = useRef(null)
  if (!blobs.current && data.length > 0) {
    blobs.current = data.map((d, i) => ({
      id: i,
      x: 10 + (i % 3) * 35 + Math.random() * 10,
      y: 15 + Math.floor(i / 3) * 50 + Math.random() * 15,
      size: 60 + Math.random() * 80,
      duration: 12 + Math.random() * 8,
      delay: i * 0.8,
      color: d.color,
    }))
  }
  const items = blobs.current || []

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {items.map(b => (
        <div
          key={b.id}
          className="absolute rounded-full blur-3xl"
          style={{
            left: `${b.x}%`,
            top: `${b.y}%`,
            width: b.size,
            height: b.size,
            backgroundColor: b.color,
            opacity: 0.12,
            animation: `blobFloat ${b.duration}s ease-in-out ${b.delay}s infinite alternate`,
          }}
        />
      ))}
    </div>
  )
}

// Animated donut — NO perpetual spin, just a smooth entrance
function AnimatedDonut({ data, size = 180, grandTotal = 0 }) {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let frame, start = null
    function animate(ts) {
      if (!start) start = ts
      const t = Math.min((ts - start) / 1800, 1)
      setProgress(easeOutCubic(t))
      if (t < 1) frame = requestAnimationFrame(animate)
    }
    frame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frame)
  }, [])

  const total = data.reduce((s, d) => s + d.awarded + d.pending + d.denied, 0)
  let cum = 0
  const segments = data.map(d => {
    const pct = (d.awarded + d.pending + d.denied) / total
    const start = cum
    cum += pct
    return { ...d, start, end: cum, pct }
  })

  const r = 70, cx = 100, cy = 100, sw = 18

  return (
    <svg width={size} height={size} viewBox="0 0 200 200" style={{ filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.08))' }}>
      {/* Background track */}
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#f1f5f9" strokeWidth={sw} />
      {/* Gradient defs */}
      <defs>
        {segments.map((seg, i) => (
          <linearGradient key={seg.name} id={`grad-${i}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={seg.color} />
            <stop offset="100%" stopColor={seg.accent} />
          </linearGradient>
        ))}
      </defs>
      {segments.map((seg, i) => {
        const startAngle = (seg.start * 360 - 90) * Math.PI / 180
        const endAngle = (seg.start + seg.pct * progress) * 360 - 90
        const endRad = endAngle * Math.PI / 180
        const largeArc = (seg.pct * progress) > 0.5 ? 1 : 0
        const x1 = cx + r * Math.cos(startAngle)
        const y1 = cy + r * Math.sin(startAngle)
        const x2 = cx + r * Math.cos(endRad)
        const y2 = cy + r * Math.sin(endRad)
        if (seg.pct * progress < 0.001) return null
        return (
          <path
            key={seg.name}
            d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`}
            fill="none"
            stroke={`url(#grad-${i})`}
            strokeWidth={sw}
            strokeLinecap="round"
          />
        )
      })}
      {/* Center text */}
      <text x={cx} y={cy - 6} textAnchor="middle" className="text-2xl font-bold" fill="#1e293b" fontSize="18">{fmt(grandTotal)}</text>
      <text x={cx} y={cy + 12} textAnchor="middle" fill="#94a3b8" fontSize="9">Total Pipeline</text>
    </svg>
  )
}

// Animated wave bars
function WaveBars({ data }) {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let frame, start = null
    function animate(ts) {
      if (!start) start = ts
      const t = Math.min((ts - start) / 2000, 1)
      setProgress(easeOutCubic(t))
      if (t < 1) frame = requestAnimationFrame(animate)
    }
    frame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frame)
  }, [])

  const maxVal = Math.max(...data.map(d => d.awarded + d.pending + d.denied))

  return (
    <div className="flex items-end gap-1.5 h-24">
      {data.map((d, i) => {
        const total = d.awarded + d.pending + d.denied
        const h = (total / maxVal) * 100 * progress
        return (
          <div key={d.name} className="flex-1 flex flex-col items-center gap-1">
            <div
              className={`w-full rounded-t-lg bg-gradient-to-t ${d.gradient} transition-all duration-700`}
              style={{
                height: `${h}%`,
                minHeight: 4,
                opacity: 0.75 + progress * 0.25,
              }}
            />
          </div>
        )
      })}
    </div>
  )
}

// === MAIN COMPONENT ===
export default function GrantFunderChart() {
  const [mode, setMode] = useState('background')
  const [hoveredFunder, setHoveredFunder] = useState(null)
  const [grantFunderData, setGrantFunderData] = useState([])
  const [totals, setTotals] = useState({ awarded: 0, pending: 0, denied: 0, grand: 0 })
  const [loading, setLoading] = useState(true)
  const [dataSource, setDataSource] = useState('loading')

  useEffect(() => {
    let cancelled = false
    async function fetchFunderData() {
      try {
        const res = await apiClient.getFunderBreakdown()
        if (cancelled) return
        const { funders, summary } = res.data
        if (funders && funders.length > 0) {
          setGrantFunderData(enrichFunders(funders))
          setTotals({
            awarded: summary.total_awarded,
            pending: summary.total_pending,
            denied: summary.total_denied,
            grand: summary.total_pipeline,
          })
          setDataSource('api')
        } else {
          setGrantFunderData([])
          setTotals({ awarded: 0, pending: 0, denied: 0, grand: 0 })
          setDataSource('api')
        }
      } catch (err) {
        if (cancelled) return
        console.log('Funder breakdown API unavailable:', err.message)
        setGrantFunderData([])
        setTotals({ awarded: 0, pending: 0, denied: 0, grand: 0 })
        setDataSource('api')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    fetchFunderData()
    return () => { cancelled = true }
  }, [])

  const totalAwarded = totals.awarded
  const totalPending = totals.pending
  const totalDenied = totals.denied
  const grandTotal = totals.grand

  const handleClick = useCallback(() => {
    if (loading) return
    setMode(prev => prev === 'background' ? 'static' : prev === 'static' ? 'expanded' : 'background')
  }, [loading])

  const modeLabel = mode === 'background' ? 'Click to focus' : mode === 'static' ? 'Click to expand details' : 'Click to minimize'

  // Loading state
  if (loading) {
    return (
      <div className="relative w-full overflow-hidden rounded-2xl border border-gray-100 shadow-sm bg-white p-12 text-center">
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-t-2xl" />
        <Loader2 size={28} className="mx-auto text-blue-500 animate-spin mb-3" />
        <p className="text-sm text-gray-400 font-medium">Loading grant data...</p>
      </div>
    )
  }

  // Empty state — show the welcome hero instead of boring $0
  if (grantFunderData.length === 0) {
    return <WelcomeHero />
  }

  // Data exists — show the funder analytics chart
  return (
    <>
      <style>{`
        @keyframes blobFloat {
          0% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(15px, -20px) scale(1.15); }
          66% { transform: translate(-10px, 10px) scale(0.9); }
          100% { transform: translate(8px, -12px) scale(1.05); }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: scale(0.97); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        .anim-slide-up { animation: slideUp 0.45s ease-out forwards; }
        .anim-fade-in { animation: fadeIn 0.4s ease-out forwards; }
        .gradient-shimmer {
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
          background-size: 200% 100%;
          animation: shimmer 3s ease-in-out infinite;
        }
      `}</style>

      <div
        onClick={handleClick}
        className={`
          relative w-full overflow-hidden rounded-2xl cursor-pointer border border-gray-100
          transition-all duration-700 ease-in-out shadow-sm hover:shadow-md
          ${mode === 'background' ? 'h-52 md:h-60' : 'h-auto'}
        `}
        style={{ background: '#ffffff' }}
      >
        <GradientBlobs data={grantFunderData} />
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-t-2xl" />

        {/* ============ BACKGROUND MODE ============ */}
        {mode === 'background' && (
          <div className="absolute inset-0 flex items-center px-6 md:px-10 pt-2">
            <div className="relative z-10 hidden md:flex items-center justify-center" style={{ minWidth: 180 }}>
              <AnimatedDonut data={grantFunderData} size={170} grandTotal={grandTotal} />
            </div>

            <div className="relative z-20 flex-1 text-center px-4">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-full text-xs font-semibold text-blue-600 mb-3 border border-blue-100">
                <BarChart3 size={13} />
                Grant Funder Analytics
              </div>
              <h3 className="text-2xl md:text-3xl font-extrabold text-gray-900 mb-1.5 tracking-tight">
                {fmt(grandTotal)} <span className="text-gray-400 font-normal text-lg">Pipeline</span>
              </h3>
              <div className="flex items-center justify-center gap-5 text-sm mt-2">
                <span className="flex items-center gap-1.5 font-semibold text-emerald-600">
                  <div className="w-2 h-2 rounded-full bg-gradient-to-r from-emerald-400 to-teal-500" />
                  {fmt(totalAwarded)} awarded
                </span>
                <span className="flex items-center gap-1.5 font-medium text-amber-600">
                  <div className="w-2 h-2 rounded-full bg-gradient-to-r from-amber-400 to-orange-500" />
                  {fmt(totalPending)} pending
                </span>
                <span className="flex items-center gap-1.5 font-medium text-rose-500">
                  <div className="w-2 h-2 rounded-full bg-gradient-to-r from-rose-400 to-red-500" />
                  {fmt(totalDenied)} denied
                </span>
              </div>
            </div>

            <div className="relative z-10 w-36 md:w-48 hidden sm:block">
              <WaveBars data={grantFunderData} />
              <div className="flex justify-between mt-1.5 px-0.5">
                {grantFunderData.map(d => (
                  <div key={d.name} className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: d.color, opacity: 0.6 }} />
                ))}
              </div>
            </div>

            <div className="absolute right-4 top-1/2 -translate-y-1/2 md:hidden opacity-20">
              <AnimatedDonut data={grantFunderData} size={120} grandTotal={grandTotal} />
            </div>

            <div className="absolute bottom-3 left-0 right-0 text-center z-20">
              <span className="text-xs text-gray-400 flex items-center justify-center gap-1">
                <ChevronDown size={14} className="animate-bounce" /> {modeLabel}
              </span>
            </div>
          </div>
        )}

        {/* ============ STATIC MODE ============ */}
        {mode === 'static' && (
          <div className="relative p-6 md:p-8 pt-4 anim-fade-in">
            <div className="flex items-center justify-between mb-5">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <div className="p-1.5 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600">
                    <BarChart3 size={16} className="text-white" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">Grant Funder Overview</h3>
                </div>
                <p className="text-sm text-gray-400 ml-9">Click to see detailed breakdown</p>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="flex items-center gap-1.5 font-semibold text-emerald-600">
                  <Award size={14} /> {fmt(totalAwarded)}
                </span>
                <span className="flex items-center gap-1.5 text-amber-600">
                  <Clock size={14} /> {fmt(totalPending)}
                </span>
              </div>
            </div>

            <div className="space-y-3">
              {grantFunderData.map((d, i) => {
                const total = d.awarded + d.pending + d.denied
                const aW = (d.awarded / total) * 100
                const pW = (d.pending / total) * 100
                const dW = (d.denied / total) * 100
                const isHovered = hoveredFunder === d.name
                return (
                  <div
                    key={d.name}
                    className="anim-slide-up"
                    style={{ animationDelay: `${i * 70}ms` }}
                    onMouseEnter={() => setHoveredFunder(d.name)}
                    onMouseLeave={() => setHoveredFunder(null)}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <div className={`w-2.5 h-2.5 rounded-full bg-gradient-to-r ${d.gradient}`} />
                        <span className={`text-sm font-medium transition-colors ${isHovered ? 'text-gray-900' : 'text-gray-600'}`}>{d.name}</span>
                      </div>
                      <span className="text-xs font-semibold text-gray-500">{fmt(total)}</span>
                    </div>
                    <div className={`h-8 rounded-xl overflow-hidden flex bg-gray-50 transition-all duration-300 ${isHovered ? 'shadow-md scale-[1.01] ring-1 ring-gray-200' : ''}`}>
                      <div
                        className={`h-full bg-gradient-to-r ${d.gradient} transition-all duration-700 ease-out flex items-center justify-center relative overflow-hidden`}
                        style={{ width: `${aW}%` }}
                      >
                        <div className="absolute inset-0 gradient-shimmer" />
                        {aW > 18 && <span className="text-[10px] font-bold text-white relative z-10">{fmt(d.awarded)}</span>}
                      </div>
                      <div
                        className="h-full transition-all duration-700 ease-out flex items-center justify-center"
                        style={{ width: `${pW}%`, backgroundColor: d.color, opacity: 0.3 }}
                      >
                        {pW > 18 && <span className="text-[10px] font-bold text-gray-600">{fmt(d.pending)}</span>}
                      </div>
                      <div
                        className="h-full transition-all duration-700 ease-out flex items-center justify-center bg-gradient-to-r from-rose-300 to-red-400"
                        style={{ width: `${dW}%`, opacity: 0.35 }}
                      >
                        {dW > 14 && <span className="text-[10px] font-bold text-white/70">{fmt(d.denied)}</span>}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="flex items-center gap-6 mt-5 justify-center">
              <span className="flex items-center gap-1.5 text-xs text-gray-500 font-medium">
                <div className="w-3 h-2 rounded-sm bg-gradient-to-r from-blue-500 to-indigo-600" /> Awarded
              </span>
              <span className="flex items-center gap-1.5 text-xs text-gray-500 font-medium">
                <div className="w-3 h-2 rounded-sm bg-blue-200" /> Pending
              </span>
              <span className="flex items-center gap-1.5 text-xs text-gray-500 font-medium">
                <div className="w-3 h-2 rounded-sm bg-gradient-to-r from-rose-300 to-red-400 opacity-50" /> Denied
              </span>
            </div>

            <div className="text-center mt-4">
              <span className="text-xs text-gray-400 flex items-center justify-center gap-1">
                <ChevronDown size={14} /> {modeLabel}
              </span>
            </div>
          </div>
        )}

        {/* ============ EXPANDED MODE ============ */}
        {mode === 'expanded' && (
          <div className="relative p-6 md:p-8 pt-4 anim-fade-in">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600">
                    <BarChart3 size={16} className="text-white" />
                  </div>
                  Grant Funder Detailed Metrics
                </h3>
                <p className="text-sm text-gray-400 mt-0.5 ml-9">Full breakdown by source and status</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-extrabold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">{fmt(grandTotal)}</p>
                <p className="text-xs text-gray-400">Total Pipeline</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 mb-6">
              <div className="rounded-xl p-4 text-center anim-slide-up border border-emerald-100" style={{ animationDelay: '0ms', background: 'linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%)' }}>
                <div className="w-9 h-9 mx-auto rounded-lg bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center mb-2 shadow-lg shadow-emerald-200">
                  <Award size={18} className="text-white" />
                </div>
                <p className="text-xl font-extrabold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">{fmt(totalAwarded)}</p>
                <p className="text-xs text-gray-500 mt-0.5">Total Awarded</p>
                <div className="mt-2 h-1 rounded-full bg-gray-100 overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-teal-500" style={{ width: `${grandTotal > 0 ? Math.round((totalAwarded / grandTotal) * 100) : 0}%` }} />
                </div>
                <p className="text-[10px] text-emerald-600 font-semibold mt-1">{grandTotal > 0 ? Math.round((totalAwarded / grandTotal) * 100) : 0}% of pipeline</p>
              </div>

              <div className="rounded-xl p-4 text-center anim-slide-up border border-amber-100" style={{ animationDelay: '80ms', background: 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)' }}>
                <div className="w-9 h-9 mx-auto rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center mb-2 shadow-lg shadow-amber-200">
                  <Clock size={18} className="text-white" />
                </div>
                <p className="text-xl font-extrabold bg-gradient-to-r from-amber-600 to-orange-600 bg-clip-text text-transparent">{fmt(totalPending)}</p>
                <p className="text-xs text-gray-500 mt-0.5">Total Pending</p>
                <div className="mt-2 h-1 rounded-full bg-gray-100 overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-amber-400 to-orange-500" style={{ width: `${grandTotal > 0 ? Math.round((totalPending / grandTotal) * 100) : 0}%` }} />
                </div>
                <p className="text-[10px] text-amber-600 font-semibold mt-1">{grandTotal > 0 ? Math.round((totalPending / grandTotal) * 100) : 0}% of pipeline</p>
              </div>

              <div className="rounded-xl p-4 text-center anim-slide-up border border-rose-100" style={{ animationDelay: '160ms', background: 'linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%)' }}>
                <div className="w-9 h-9 mx-auto rounded-lg bg-gradient-to-br from-rose-400 to-red-500 flex items-center justify-center mb-2 shadow-lg shadow-rose-200">
                  <XCircle size={18} className="text-white" />
                </div>
                <p className="text-xl font-extrabold bg-gradient-to-r from-rose-600 to-red-600 bg-clip-text text-transparent">{fmt(totalDenied)}</p>
                <p className="text-xs text-gray-500 mt-0.5">Total Denied</p>
                <div className="mt-2 h-1 rounded-full bg-gray-100 overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-rose-400 to-red-500" style={{ width: `${grandTotal > 0 ? Math.round((totalDenied / grandTotal) * 100) : 0}%` }} />
                </div>
                <p className="text-[10px] text-rose-600 font-semibold mt-1">{grandTotal > 0 ? Math.round((totalDenied / grandTotal) * 100) : 0}% of pipeline</p>
              </div>
            </div>

            <div className="rounded-xl border border-gray-100 overflow-hidden shadow-sm">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gradient-to-r from-gray-50 to-slate-50 border-b border-gray-100">
                    <th className="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wider">Funder</th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wider hidden sm:table-cell">Category</th>
                    <th className="text-right px-4 py-3 font-semibold text-emerald-600 text-xs uppercase tracking-wider">Awarded</th>
                    <th className="text-right px-4 py-3 font-semibold text-amber-600 text-xs uppercase tracking-wider">Pending</th>
                    <th className="text-right px-4 py-3 font-semibold text-rose-600 text-xs uppercase tracking-wider hidden sm:table-cell">Denied</th>
                    <th className="text-right px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wider">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {grantFunderData.map((d, i) => {
                    const total = d.awarded + d.pending + d.denied
                    const successRate = total > 0 ? Math.round((d.awarded / total) * 100) : 0
                    return (
                      <tr
                        key={d.name}
                        className="border-b border-gray-50 hover:bg-blue-50/30 transition-colors anim-slide-up"
                        style={{ animationDelay: `${(i + 3) * 50}ms` }}
                      >
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-2.5">
                            <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${d.gradient}`} />
                            <span className="font-semibold text-gray-800">{d.name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3.5 hidden sm:table-cell">
                          <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-500 font-medium">{d.category}</span>
                        </td>
                        <td className="px-4 py-3.5 text-right font-semibold text-emerald-600">{fmt(d.awarded)}</td>
                        <td className="px-4 py-3.5 text-right text-amber-600">{fmt(d.pending)}</td>
                        <td className="px-4 py-3.5 text-right text-rose-500 hidden sm:table-cell">{fmt(d.denied)}</td>
                        <td className="px-4 py-3.5 text-right">
                          <span className="font-bold text-gray-900">{fmt(total)}</span>
                          <span className={`ml-2 text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${
                            successRate >= 60 ? 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                            : successRate >= 40 ? 'bg-amber-50 text-amber-600 border border-amber-200'
                            : 'bg-rose-50 text-rose-600 border border-rose-200'
                          }`}>
                            {successRate}%
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
                <tfoot>
                  <tr className="bg-gradient-to-r from-gray-50 to-slate-50 font-bold border-t border-gray-200">
                    <td className="px-4 py-3 text-gray-900">Total</td>
                    <td className="px-4 py-3 hidden sm:table-cell" />
                    <td className="px-4 py-3 text-right text-emerald-600">{fmt(totalAwarded)}</td>
                    <td className="px-4 py-3 text-right text-amber-600">{fmt(totalPending)}</td>
                    <td className="px-4 py-3 text-right text-rose-500 hidden sm:table-cell">{fmt(totalDenied)}</td>
                    <td className="px-4 py-3 text-right text-gray-900 text-base">{fmt(grandTotal)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div className="text-center mt-5">
              <span className="text-xs text-gray-400 flex items-center justify-center gap-1 hover:text-gray-600 transition-colors">
                <ChevronUp size={14} /> {modeLabel}
              </span>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
