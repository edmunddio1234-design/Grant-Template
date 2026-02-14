import { useState, useEffect, useRef, useCallback } from 'react'
import { DollarSign, TrendingUp, Award, Clock, XCircle, ChevronDown, ChevronUp, BarChart3 } from 'lucide-react'

// Grant/Funder data for the animated chart
const grantFunderData = [
  { name: 'Federal Grants', awarded: 285000, pending: 150000, denied: 45000, category: 'Government', color: '#3B82F6', accent: '#60A5FA' },
  { name: 'State LCTF', awarded: 125000, pending: 75000, denied: 20000, category: 'Government', color: '#8B5CF6', accent: '#A78BFA' },
  { name: 'Corporate Sponsors', awarded: 180000, pending: 95000, denied: 30000, category: 'Corporate', color: '#10B981', accent: '#34D399' },
  { name: 'Foundation Grants', awarded: 92000, pending: 55000, denied: 15000, category: 'Foundation', color: '#F59E0B', accent: '#FBBF24' },
  { name: 'Community Fund', awarded: 37750, pending: 28000, denied: 8000, category: 'Community', color: '#EC4899', accent: '#F472B6' },
  { name: 'United Way', awarded: 65000, pending: 40000, denied: 12000, category: 'Nonprofit', color: '#06B6D4', accent: '#22D3EE' },
]

const totalAwarded = grantFunderData.reduce((s, d) => s + d.awarded, 0)
const totalPending = grantFunderData.reduce((s, d) => s + d.pending, 0)
const totalDenied = grantFunderData.reduce((s, d) => s + d.denied, 0)
const grandTotal = totalAwarded + totalPending + totalDenied

function formatCurrency(val) {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}

// Animated floating particles for background mode
function FloatingParticles({ count = 20 }) {
  const particles = useRef(
    Array.from({ length: count }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 4 + 2,
      duration: Math.random() * 15 + 10,
      delay: Math.random() * 5,
      opacity: Math.random() * 0.3 + 0.1,
      color: grantFunderData[i % grantFunderData.length].color
    }))
  ).current

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map(p => (
        <div
          key={p.id}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            backgroundColor: p.color,
            opacity: p.opacity,
            animation: `floatParticle ${p.duration}s ease-in-out ${p.delay}s infinite alternate`
          }}
        />
      ))}
    </div>
  )
}

// Animated bar segments for background
function AnimatedBars({ data, animate = true }) {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!animate) { setProgress(1); return }
    let frame
    let start = null
    const duration = 2000
    function step(ts) {
      if (!start) start = ts
      const elapsed = ts - start
      const p = Math.min(elapsed / duration, 1)
      setProgress(easeOutCubic(p))
      if (p < 1) frame = requestAnimationFrame(step)
    }
    frame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frame)
  }, [animate])

  return (
    <div className="w-full space-y-2">
      {data.map((d, i) => {
        const total = d.awarded + d.pending + d.denied
        const awardedW = (d.awarded / grandTotal) * 100 * progress
        const pendingW = (d.pending / grandTotal) * 100 * progress
        const deniedW = (d.denied / grandTotal) * 100 * progress
        return (
          <div key={d.name} className="relative" style={{ animationDelay: `${i * 120}ms` }}>
            <div className="h-6 md:h-8 rounded-lg overflow-hidden bg-white/5 flex" style={{ opacity: 0.6 + progress * 0.4 }}>
              <div
                className="h-full transition-all duration-1000 ease-out"
                style={{ width: `${awardedW}%`, backgroundColor: d.color, opacity: 0.9 }}
              />
              <div
                className="h-full transition-all duration-1000 ease-out"
                style={{ width: `${pendingW}%`, backgroundColor: d.accent, opacity: 0.6 }}
              />
              <div
                className="h-full transition-all duration-1000 ease-out"
                style={{ width: `${deniedW}%`, backgroundColor: '#EF4444', opacity: 0.35 }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3)
}

// Donut ring for background mode
function AnimatedDonut({ data, size = 200 }) {
  const [rotation, setRotation] = useState(0)
  const animRef = useRef()

  useEffect(() => {
    let frame
    function tick() {
      setRotation(r => (r + 0.15) % 360)
      frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [])

  const total = data.reduce((s, d) => s + d.awarded + d.pending + d.denied, 0)
  let cumulative = 0
  const segments = data.map((d, i) => {
    const val = d.awarded + d.pending + d.denied
    const pct = val / total
    const startAngle = cumulative * 360
    cumulative += pct
    const endAngle = cumulative * 360
    return { ...d, startAngle, endAngle, pct }
  })

  const r = 80
  const cx = 100
  const cy = 100
  const strokeWidth = 24

  return (
    <svg width={size} height={size} viewBox="0 0 200 200" className="drop-shadow-lg" style={{ transform: `rotate(${rotation}deg)` }}>
      {segments.map((seg, i) => {
        const startRad = (seg.startAngle - 90) * Math.PI / 180
        const endRad = (seg.endAngle - 90) * Math.PI / 180
        const largeArc = seg.pct > 0.5 ? 1 : 0
        const x1 = cx + r * Math.cos(startRad)
        const y1 = cy + r * Math.sin(startRad)
        const x2 = cx + r * Math.cos(endRad)
        const y2 = cy + r * Math.sin(endRad)
        return (
          <path
            key={seg.name}
            d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`}
            fill="none"
            stroke={seg.color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            opacity={0.7}
          />
        )
      })}
    </svg>
  )
}

// === MAIN COMPONENT ===
export default function GrantFunderChart() {
  // 3 modes: 'background' | 'static' | 'expanded'
  const [mode, setMode] = useState('background')
  const [hoveredFunder, setHoveredFunder] = useState(null)
  const [animKey, setAnimKey] = useState(0)
  const containerRef = useRef(null)

  const handleClick = useCallback(() => {
    setMode(prev => {
      if (prev === 'background') return 'static'
      if (prev === 'static') return 'expanded'
      return 'background'
    })
    setAnimKey(k => k + 1)
  }, [])

  const modeLabel = mode === 'background' ? 'Click to focus' : mode === 'static' ? 'Click to expand details' : 'Click to minimize'

  return (
    <>
      {/* Inline keyframes */}
      <style>{`
        @keyframes floatParticle {
          0% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(12px, -18px) scale(1.3); }
          100% { transform: translate(-8px, 14px) scale(0.8); }
        }
        @keyframes pulseGlow {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 0.6; }
        }
        @keyframes slideInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeScale {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        .animate-slide-in { animation: slideInUp 0.5s ease-out forwards; }
        .animate-fade-scale { animation: fadeScale 0.4s ease-out forwards; }
      `}</style>

      <div
        ref={containerRef}
        onClick={handleClick}
        className={`
          relative w-full overflow-hidden rounded-2xl cursor-pointer
          transition-all duration-700 ease-in-out
          ${mode === 'background'
            ? 'h-48 md:h-56'
            : mode === 'static'
              ? 'h-auto min-h-[320px]'
              : 'h-auto min-h-[500px]'
          }
        `}
        style={{
          background: mode === 'background'
            ? 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)'
            : mode === 'static'
              ? 'linear-gradient(135deg, #0f172a 0%, #1a2744 60%, #1e293b 100%)'
              : 'linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e293b 100%)'
        }}
      >
        {/* ============ BACKGROUND MODE ============ */}
        {mode === 'background' && (
          <div className="absolute inset-0 flex items-center justify-between px-6 md:px-10">
            <FloatingParticles count={18} />

            {/* Left: animated donut */}
            <div className="relative z-10 opacity-50 hidden md:block">
              <AnimatedDonut data={grantFunderData} size={160} />
            </div>

            {/* Center content overlay */}
            <div className="relative z-20 flex-1 text-center">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full text-xs text-blue-300 mb-2 backdrop-blur-sm">
                <BarChart3 size={12} />
                <span>Grant Funder Analytics</span>
              </div>
              <h3 className="text-xl md:text-2xl font-bold text-white/90 mb-1">
                {formatCurrency(grandTotal)} Total Pipeline
              </h3>
              <p className="text-sm text-slate-400">
                {grantFunderData.length} funding sources tracked
              </p>
            </div>

            {/* Right: animated bars preview */}
            <div className="relative z-10 w-40 md:w-56 opacity-40 hidden sm:block">
              <AnimatedBars data={grantFunderData} animate={true} />
            </div>

            {/* Bottom hint */}
            <div className="absolute bottom-3 left-0 right-0 text-center z-20">
              <span className="text-xs text-slate-500 flex items-center justify-center gap-1">
                <ChevronDown size={14} className="animate-bounce" /> {modeLabel}
              </span>
            </div>

            {/* Glow effect */}
            <div
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full pointer-events-none"
              style={{
                background: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)',
                animation: 'pulseGlow 4s ease-in-out infinite'
              }}
            />
          </div>
        )}

        {/* ============ STATIC MODE ============ */}
        {mode === 'static' && (
          <div className="p-6 md:p-8 animate-fade-scale">
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <BarChart3 size={20} className="text-blue-400" />
                  <h3 className="text-lg font-bold text-white">Grant Funder Overview</h3>
                </div>
                <p className="text-sm text-slate-400">Click to see detailed breakdown</p>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <Award size={14} /> {formatCurrency(totalAwarded)}
                </span>
                <span className="flex items-center gap-1.5 text-amber-400">
                  <Clock size={14} /> {formatCurrency(totalPending)}
                </span>
                <span className="flex items-center gap-1.5 text-red-400">
                  <XCircle size={14} /> {formatCurrency(totalDenied)}
                </span>
              </div>
            </div>

            {/* Stacked bars with labels */}
            <div className="space-y-3">
              {grantFunderData.map((d, i) => {
                const total = d.awarded + d.pending + d.denied
                const aW = (d.awarded / total) * 100
                const pW = (d.pending / total) * 100
                const dW = (d.denied / total) * 100
                return (
                  <div
                    key={d.name}
                    className="animate-slide-in"
                    style={{ animationDelay: `${i * 80}ms` }}
                    onMouseEnter={() => setHoveredFunder(d.name)}
                    onMouseLeave={() => setHoveredFunder(null)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-slate-300">{d.name}</span>
                      <span className="text-xs text-slate-500">{formatCurrency(total)}</span>
                    </div>
                    <div className={`h-7 rounded-lg overflow-hidden flex transition-all duration-300 ${hoveredFunder === d.name ? 'ring-1 ring-white/20 scale-[1.01]' : ''}`}>
                      <div
                        className="h-full transition-all duration-700 ease-out flex items-center justify-center"
                        style={{ width: `${aW}%`, backgroundColor: d.color }}
                      >
                        {aW > 15 && <span className="text-[10px] font-bold text-white/90">{formatCurrency(d.awarded)}</span>}
                      </div>
                      <div
                        className="h-full transition-all duration-700 ease-out flex items-center justify-center"
                        style={{ width: `${pW}%`, backgroundColor: d.accent, opacity: 0.7 }}
                      >
                        {pW > 15 && <span className="text-[10px] font-bold text-white/80">{formatCurrency(d.pending)}</span>}
                      </div>
                      <div
                        className="h-full transition-all duration-700 ease-out flex items-center justify-center"
                        style={{ width: `${dW}%`, backgroundColor: '#EF4444', opacity: 0.5 }}
                      >
                        {dW > 12 && <span className="text-[10px] font-bold text-white/70">{formatCurrency(d.denied)}</span>}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Legend */}
            <div className="flex items-center gap-6 mt-5 justify-center">
              <span className="flex items-center gap-1.5 text-xs text-slate-400">
                <div className="w-3 h-3 rounded-sm bg-blue-500" /> Awarded
              </span>
              <span className="flex items-center gap-1.5 text-xs text-slate-400">
                <div className="w-3 h-3 rounded-sm bg-blue-300 opacity-70" /> Pending
              </span>
              <span className="flex items-center gap-1.5 text-xs text-slate-400">
                <div className="w-3 h-3 rounded-sm bg-red-500 opacity-50" /> Denied
              </span>
            </div>

            <div className="text-center mt-4">
              <span className="text-xs text-slate-500 flex items-center justify-center gap-1">
                <ChevronDown size={14} /> {modeLabel}
              </span>
            </div>
          </div>
        )}

        {/* ============ EXPANDED MODE ============ */}
        {mode === 'expanded' && (
          <div className="p-6 md:p-8 animate-fade-scale">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <BarChart3 size={20} className="text-blue-400" />
                  Grant Funder Detailed Metrics
                </h3>
                <p className="text-sm text-slate-400 mt-0.5">Full breakdown by source and status</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-white">{formatCurrency(grandTotal)}</p>
                <p className="text-xs text-slate-400">Total Pipeline Value</p>
              </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-3 gap-3 mb-6">
              <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center animate-slide-in" style={{ animationDelay: '0ms' }}>
                <Award size={20} className="mx-auto text-emerald-400 mb-1" />
                <p className="text-xl font-bold text-emerald-400">{formatCurrency(totalAwarded)}</p>
                <p className="text-xs text-slate-400 mt-0.5">Total Awarded</p>
                <p className="text-xs text-emerald-500 mt-1">{Math.round((totalAwarded / grandTotal) * 100)}% of pipeline</p>
              </div>
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 text-center animate-slide-in" style={{ animationDelay: '100ms' }}>
                <Clock size={20} className="mx-auto text-amber-400 mb-1" />
                <p className="text-xl font-bold text-amber-400">{formatCurrency(totalPending)}</p>
                <p className="text-xs text-slate-400 mt-0.5">Total Pending</p>
                <p className="text-xs text-amber-500 mt-1">{Math.round((totalPending / grandTotal) * 100)}% of pipeline</p>
              </div>
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-center animate-slide-in" style={{ animationDelay: '200ms' }}>
                <XCircle size={20} className="mx-auto text-red-400 mb-1" />
                <p className="text-xl font-bold text-red-400">{formatCurrency(totalDenied)}</p>
                <p className="text-xs text-slate-400 mt-0.5">Total Denied</p>
                <p className="text-xs text-red-500 mt-1">{Math.round((totalDenied / grandTotal) * 100)}% of pipeline</p>
              </div>
            </div>

            {/* Detailed Table */}
            <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-slate-400">
                    <th className="text-left px-4 py-3 font-medium">Funder</th>
                    <th className="text-left px-4 py-3 font-medium hidden sm:table-cell">Category</th>
                    <th className="text-right px-4 py-3 font-medium">Awarded</th>
                    <th className="text-right px-4 py-3 font-medium">Pending</th>
                    <th className="text-right px-4 py-3 font-medium hidden sm:table-cell">Denied</th>
                    <th className="text-right px-4 py-3 font-medium">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {grantFunderData.map((d, i) => {
                    const total = d.awarded + d.pending + d.denied
                    const successRate = Math.round((d.awarded / total) * 100)
                    return (
                      <tr
                        key={d.name}
                        className="border-b border-white/5 hover:bg-white/5 transition-colors animate-slide-in"
                        style={{ animationDelay: `${(i + 3) * 60}ms` }}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                            <span className="font-medium text-white">{d.name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-slate-400 hidden sm:table-cell">{d.category}</td>
                        <td className="px-4 py-3 text-right text-emerald-400 font-medium">{formatCurrency(d.awarded)}</td>
                        <td className="px-4 py-3 text-right text-amber-400">{formatCurrency(d.pending)}</td>
                        <td className="px-4 py-3 text-right text-red-400 hidden sm:table-cell">{formatCurrency(d.denied)}</td>
                        <td className="px-4 py-3 text-right">
                          <span className="text-white font-medium">{formatCurrency(total)}</span>
                          <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${successRate >= 60 ? 'bg-emerald-500/20 text-emerald-400' : successRate >= 40 ? 'bg-amber-500/20 text-amber-400' : 'bg-red-500/20 text-red-400'}`}>
                            {successRate}%
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
                <tfoot>
                  <tr className="border-t border-white/10 bg-white/5 font-bold">
                    <td className="px-4 py-3 text-white">Total</td>
                    <td className="px-4 py-3 hidden sm:table-cell" />
                    <td className="px-4 py-3 text-right text-emerald-400">{formatCurrency(totalAwarded)}</td>
                    <td className="px-4 py-3 text-right text-amber-400">{formatCurrency(totalPending)}</td>
                    <td className="px-4 py-3 text-right text-red-400 hidden sm:table-cell">{formatCurrency(totalDenied)}</td>
                    <td className="px-4 py-3 text-right text-white">{formatCurrency(grandTotal)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div className="text-center mt-4">
              <span className="text-xs text-slate-500 flex items-center justify-center gap-1">
                <ChevronUp size={14} /> {modeLabel}
              </span>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
