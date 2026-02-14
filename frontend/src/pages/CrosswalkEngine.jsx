import { useState, useMemo, useEffect } from 'react'
import { Download, Filter } from 'lucide-react'
import RiskBadge from '../components/common/RiskBadge'
import Modal from '../components/common/Modal'
import toast from 'react-hot-toast'
import { apiClient } from '../api/client'

const defaultRFPs = [
  { id: 'demo-1', name: 'Community Foundation Grant 2024' },
  { id: 'demo-2', name: 'Department of Family Services RFP' },
  { id: 'demo-3', name: 'Local Nonprofit Partnership Grant' }
]

const mockMappings = [
  {
    id: 1,
    requirement: 'Demonstrate clear organizational mission focused on family strengthening',
    boilerplateMatches: ['Organizational History and Mission', 'Project Family Build Program Overview'],
    riskLevel: 'green',
    alignmentScore: 92,
    notes: 'Strong alignment with FOAM mission and programs',
    status: 'approved'
  },
  {
    id: 2,
    requirement: 'Provide evidence of program effectiveness through evaluation data',
    boilerplateMatches: ['Evaluation and Outcomes Framework'],
    riskLevel: 'yellow',
    alignmentScore: 68,
    notes: 'Need more outcome metrics and data',
    status: 'pending'
  },
  {
    id: 3,
    requirement: 'Organizational capacity to serve 500+ participants annually',
    boilerplateMatches: ['Organizational Capacity and Infrastructure'],
    riskLevel: 'green',
    alignmentScore: 88,
    notes: 'FOAM infrastructure documented and verified',
    status: 'approved'
  },
  {
    id: 4,
    requirement: 'Staff qualifications and experience in family services',
    boilerplateMatches: ['Project Family Build Program Overview', 'Responsible Fatherhood Classes Curriculum'],
    riskLevel: 'yellow',
    alignmentScore: 75,
    notes: 'Good coverage but need staff bios section',
    status: 'pending'
  },
  {
    id: 5,
    requirement: 'Evidence of community partnerships and collaboration',
    boilerplateMatches: [],
    riskLevel: 'red',
    alignmentScore: 0,
    notes: 'Gap identified - need community partnership section',
    status: 'pending'
  },
  {
    id: 6,
    requirement: 'Sustainability plan for program continuation beyond grant period',
    boilerplateMatches: [],
    riskLevel: 'red',
    alignmentScore: 15,
    notes: 'Critical gap - must develop sustainability narrative',
    status: 'pending'
  },
  {
    id: 7,
    requirement: 'Celebration and recognition of fatherhood achievements',
    boilerplateMatches: ['Celebration of Fatherhood Events'],
    riskLevel: 'green',
    alignmentScore: 85,
    notes: 'Perfect match with Celebration Events program',
    status: 'approved'
  },
  {
    id: 8,
    requirement: 'Budget narrative justifying all expenses',
    boilerplateMatches: [],
    riskLevel: 'yellow',
    alignmentScore: 30,
    notes: 'Partial content available, needs expansion',
    status: 'pending'
  }
]

export default function CrosswalkEngine() {
  const [rfpList, setRfpList] = useState(defaultRFPs)
  const [selectedRFP, setSelectedRFP] = useState(null)
  const [mappings, setMappings] = useState(mockMappings)
  const [riskFilter, setRiskFilter] = useState('all')
  const [selectedMapping, setSelectedMapping] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [editingMapping, setEditingMapping] = useState(null)

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
          setSelectedRFP(defaultRFPs[0].id)
        }
      } catch (err) {
        console.log('RFP list unavailable, using defaults:', err.message)
        setSelectedRFP(defaultRFPs[0].id)
      }
    }
    fetchRFPs()
  }, [])

  // Fetch crosswalk data from API when RFP changes
  useEffect(() => {
    if (!selectedRFP) return
    async function fetchCrosswalk() {
      try {
        const res = await apiClient.getCrosswalkMatrix(selectedRFP)
        const data = res.data
        if (Array.isArray(data) && data.length > 0) {
          setMappings(data.map(m => ({
            id: m.id,
            requirement: m.requirement_text || m.requirement || '',
            boilerplateMatches: m.matched_sections || m.boilerplate_matches || [],
            riskLevel: m.risk_level || 'yellow',
            alignmentScore: m.alignment_score || 0,
            notes: m.notes || '',
            status: m.status || 'pending'
          })))
        }
      } catch (err) {
        console.log('Crosswalk API unavailable, using mock data:', err.message)
      }
    }
    fetchCrosswalk()
  }, [selectedRFP])

  const filteredMappings = useMemo(() => {
    if (riskFilter === 'all') return mappings
    return mappings.filter((m) => m.riskLevel === riskFilter)
  }, [mappings, riskFilter])

  const stats = useMemo(() => {
    return {
      strongMatches: mappings.filter((m) => m.riskLevel === 'green').length,
      partialMatches: mappings.filter((m) => m.riskLevel === 'yellow').length,
      gaps: mappings.filter((m) => m.riskLevel === 'red').length,
      avgScore: Math.round(mappings.reduce((acc, m) => acc + m.alignmentScore, 0) / mappings.length)
    }
  }, [mappings])

  const handleApproveMapping = async (id) => {
    try {
      await apiClient.approveCrosswalkMapping(id)
    } catch (err) {
      console.log('Approve API failed, updating locally:', err.message)
    }
    const updated = mappings.map((m) =>
      m.id === id ? { ...m, status: 'approved' } : m
    )
    setMappings(updated)
    toast.success('Mapping approved')
  }

  const handleRejectMapping = (id) => {
    const updated = mappings.map((m) =>
      m.id === id ? { ...m, status: 'rejected' } : m
    )
    setMappings(updated)
    toast.error('Mapping rejected')
  }

  const handleEditMapping = (mapping) => {
    setEditingMapping(mapping)
    setSelectedMapping(mapping)
    setShowModal(true)
  }

  const handleSaveMapping = () => {
    if (editingMapping) {
      const updated = mappings.map((m) =>
        m.id === editingMapping.id ? editingMapping : m
      )
      setMappings(updated)
      setShowModal(false)
      setEditingMapping(null)
      toast.success('Mapping updated')
    }
  }

  const handleExport = async () => {
    try {
      await apiClient.exportCrosswalk(selectedRFP, 'csv')
      toast.success('Exporting crosswalk matrix as CSV')
    } catch (err) {
      console.log('Export API failed:', err.message)
      toast.success('Exporting crosswalk matrix as CSV (demo)')
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="section-title">Crosswalk Engine</h2>
          <p className="text-gray-600 mt-2">Map RFP requirements to FOAM boilerplate content</p>
        </div>
        <button onClick={handleExport} className="btn-primary">
          <Download size={20} />
          Export Matrix
        </button>
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

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="p-6">
            <p className="text-sm font-medium text-gray-600">Strong Matches</p>
            <p className="text-3xl font-bold text-emerald-600 mt-2">{stats.strongMatches}</p>
            <p className="text-xs text-gray-500 mt-2">Green risk level</p>
          </div>
        </div>

        <div className="card">
          <div className="p-6">
            <p className="text-sm font-medium text-gray-600">Partial Matches</p>
            <p className="text-3xl font-bold text-amber-600 mt-2">{stats.partialMatches}</p>
            <p className="text-xs text-gray-500 mt-2">Yellow risk level</p>
          </div>
        </div>

        <div className="card">
          <div className="p-6">
            <p className="text-sm font-medium text-gray-600">Critical Gaps</p>
            <p className="text-3xl font-bold text-red-600 mt-2">{stats.gaps}</p>
            <p className="text-xs text-gray-500 mt-2">Red risk level</p>
          </div>
        </div>

        <div className="card">
          <div className="p-6">
            <p className="text-sm font-medium text-gray-600">Average Score</p>
            <p className="text-3xl font-bold text-foam-primary mt-2">{stats.avgScore}%</p>
            <p className="text-xs text-gray-500 mt-2">Across all mappings</p>
          </div>
        </div>
      </div>

      {/* Filter */}
      <div className="card">
        <div className="p-6 flex items-center gap-4">
          <Filter size={20} className="text-gray-600" />
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="input-field max-w-md"
          >
            <option value="all">Show All Requirements ({mappings.length})</option>
            <option value="green">Strong Matches ({stats.strongMatches})</option>
            <option value="yellow">Partial Matches ({stats.partialMatches})</option>
            <option value="red">Critical Gaps ({stats.gaps})</option>
          </select>
        </div>
      </div>

      {/* Mappings */}
      <div className="space-y-4">
        {filteredMappings.map((mapping) => (
          <div key={mapping.id} className="card-hover">
            <div className="p-6">
              {/* Requirement */}
              <div className="mb-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900 text-lg">{mapping.requirement}</p>
                  </div>
                  <RiskBadge level={mapping.riskLevel} showIcon={true} />
                </div>
              </div>

              {/* Alignment Score */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Alignment Score</span>
                  <span className="text-lg font-bold text-foam-primary">{mapping.alignmentScore}%</span>
                </div>
                <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={clsx(
                      'h-full rounded-full transition-all',
                      mapping.riskLevel === 'green' && 'bg-emerald-500',
                      mapping.riskLevel === 'yellow' && 'bg-amber-500',
                      mapping.riskLevel === 'red' && 'bg-red-500'
                    )}
                    style={{ width: `${mapping.alignmentScore}%` }}
                  />
                </div>
              </div>

              {/* Matched Boilerplate Sections */}
              <div className="mb-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Matched Boilerplate Sections</p>
                {mapping.boilerplateMatches.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {mapping.boilerplateMatches.map((section, index) => (
                      <span key={index} className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                        {section}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-red-600 font-medium">No matching sections found</p>
                )}
              </div>

              {/* Notes */}
              <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-700">
                  <span className="font-medium">Notes:</span> {mapping.notes}
                </p>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <span className={clsx(
                  'text-sm font-medium px-3 py-1 rounded-full',
                  mapping.status === 'approved' && 'bg-emerald-100 text-emerald-800',
                  mapping.status === 'rejected' && 'bg-red-100 text-red-800',
                  mapping.status === 'pending' && 'bg-amber-100 text-amber-800'
                )}>
                  {mapping.status.charAt(0).toUpperCase() + mapping.status.slice(1)}
                </span>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleEditMapping(mapping)}
                    className="btn-secondary btn-sm"
                  >
                    Edit
                  </button>
                  {mapping.status !== 'approved' && (
                    <button
                      onClick={() => handleApproveMapping(mapping.id)}
                      className="btn-accent btn-sm"
                    >
                      Approve
                    </button>
                  )}
                  {mapping.status === 'approved' && (
                    <button
                      onClick={() => handleRejectMapping(mapping.id)}
                      className="btn-secondary btn-sm"
                    >
                      Reject
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Edit Modal */}
      {editingMapping && (
        <Modal
          open={showModal}
          onClose={() => {
            setShowModal(false)
            setEditingMapping(null)
          }}
          title="Edit Mapping"
          size="lg"
          footer={
            <>
              <button
                onClick={() => {
                  setShowModal(false)
                  setEditingMapping(null)
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button onClick={handleSaveMapping} className="btn-primary">
                Save Mapping
              </button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">Requirement</label>
              <textarea
                value={editingMapping.requirement}
                onChange={(e) => setEditingMapping({ ...editingMapping, requirement: e.target.value })}
                className="input-field h-20"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">Alignment Score</label>
              <input
                type="range"
                min="0"
                max="100"
                value={editingMapping.alignmentScore}
                onChange={(e) => setEditingMapping({ ...editingMapping, alignmentScore: Number(e.target.value) })}
                className="w-full"
              />
              <p className="text-sm text-gray-600 mt-2">{editingMapping.alignmentScore}%</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">Risk Level</label>
              <select
                value={editingMapping.riskLevel}
                onChange={(e) => setEditingMapping({ ...editingMapping, riskLevel: e.target.value })}
                className="input-field"
              >
                <option value="green">Green (Strong)</option>
                <option value="yellow">Yellow (Partial)</option>
                <option value="red">Red (Gap)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">Notes</label>
              <textarea
                value={editingMapping.notes}
                onChange={(e) => setEditingMapping({ ...editingMapping, notes: e.target.value })}
                className="input-field h-20"
              />
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

function clsx(...classes) {
  return classes.filter(Boolean).join(' ')
}
