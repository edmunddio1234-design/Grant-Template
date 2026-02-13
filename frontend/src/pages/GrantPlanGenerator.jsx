import { useState } from 'react'
import { Plus, Download, Printer, CheckCircle, Circle, AlertCircle } from 'lucide-react'
import Modal from '../components/common/Modal'
import StatusIndicator from '../components/common/StatusIndicator'
import toast from 'react-hot-toast'

const mockPlans = [
  {
    id: 1,
    name: 'Community Foundation Grant 2024',
    rfp: 'Community Foundation Grant 2024',
    status: 'draft',
    createdDate: '2024-02-12',
    lastModified: '2024-02-12',
    wordCount: 2450,
    wordTarget: 5000
  },
  {
    id: 2,
    name: 'DFS Grant - Project Family Build Track',
    rfp: 'Department of Family Services RFP',
    status: 'review',
    createdDate: '2024-02-10',
    lastModified: '2024-02-12',
    wordCount: 4850,
    wordTarget: 7500
  }
]

const mockPlanSections = [
  { id: 1, title: 'Executive Summary', words: 280, target: 250, complete: true, alignmentScore: 95 },
  { id: 2, title: 'Organizational Background', words: 420, target: 500, complete: true, alignmentScore: 88 },
  { id: 3, title: 'Project Description', words: 1200, target: 1500, complete: true, alignmentScore: 82 },
  { id: 4, title: 'Evaluation Plan', words: 380, target: 750, complete: false, alignmentScore: 65 },
  { id: 5, title: 'Budget Narrative', words: 170, target: 400, complete: false, alignmentScore: 45 }
]

const statusConfig = {
  draft: 'draft',
  review: 'pending',
  approved: 'active',
  submitted: 'published'
}

export default function GrantPlanGenerator() {
  const [plans, setPlans] = useState(mockPlans)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [showPlanDetail, setShowPlanDetail] = useState(false)
  const [formData, setFormData] = useState({
    rfpId: 1,
    programFocus: 'All Programs'
  })

  const handleGeneratePlan = () => {
    if (!formData.rfpId) {
      toast.error('Please select an RFP')
      return
    }

    const newPlan = {
      id: Math.max(...plans.map((p) => p.id)) + 1,
      name: `New Plan - ${new Date().toLocaleDateString()}`,
      rfp: 'Community Foundation Grant 2024',
      status: 'draft',
      createdDate: new Date().toISOString().split('T')[0],
      lastModified: new Date().toISOString().split('T')[0],
      wordCount: 0,
      wordTarget: 5000
    }
    setPlans([newPlan, ...plans])
    setShowGenerateModal(false)
    toast.success('Plan generated successfully')
  }

  const handleUpdateStatus = (planId, newStatus) => {
    const updated = plans.map((p) =>
      p.id === planId ? { ...p, status: newStatus } : p
    )
    setPlans(updated)
    toast.success(`Plan status updated to ${newStatus}`)
  }

  const handleExportPlan = (planId) => {
    toast.success('Exporting plan to DOCX format')
  }

  const handlePrintPlan = (planId) => {
    toast.success('Opening print preview')
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="section-title">Grant Plan Generator</h2>
          <p className="text-gray-600 mt-2">Create and manage grant application plans</p>
        </div>
        <button onClick={() => setShowGenerateModal(true)} className="btn-primary">
          <Plus size={20} />
          Generate Plan
        </button>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {plans.map((plan) => (
          <div key={plan.id} className="card-hover cursor-pointer" onClick={() => {
            setSelectedPlan(plan)
            setShowPlanDetail(true)
          }}>
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 text-lg">{plan.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{plan.rfp}</p>
                </div>
                <StatusIndicator status={statusConfig[plan.status]} size="sm" />
              </div>

              {/* Word Count Progress */}
              <div className="mb-4">
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Content Progress</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {plan.wordCount}/{plan.wordTarget} words
                  </span>
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-foam-primary rounded-full transition-all"
                    style={{ width: `${(plan.wordCount / plan.wordTarget) * 100}%` }}
                  />
                </div>
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-3 text-sm text-gray-600 mb-4">
                <div>
                  <p className="text-xs text-gray-500">Created</p>
                  <p className="font-medium text-gray-900">{plan.createdDate}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Last Modified</p>
                  <p className="font-medium text-gray-900">{plan.lastModified}</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 pt-4 border-t border-gray-200">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleExportPlan(plan.id)
                  }}
                  className="flex-1 btn-secondary btn-sm"
                >
                  <Download size={16} />
                  Export
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handlePrintPlan(plan.id)
                  }}
                  className="flex-1 btn-secondary btn-sm"
                >
                  <Printer size={16} />
                  Print
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Generate Modal */}
      <Modal
        open={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        title="Generate New Plan"
        size="md"
        footer={
          <>
            <button onClick={() => setShowGenerateModal(false)} className="btn-secondary">
              Cancel
            </button>
            <button onClick={handleGeneratePlan} className="btn-primary">
              Generate Plan
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Select RFP</label>
            <select
              value={formData.rfpId}
              onChange={(e) => setFormData({ ...formData, rfpId: Number(e.target.value) })}
              className="input-field"
            >
              <option value="">-- Choose an RFP --</option>
              <option value={1}>Community Foundation Grant 2024</option>
              <option value={2}>Department of Family Services RFP</option>
              <option value={3}>Local Nonprofit Partnership Grant</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Program Focus</label>
            <select
              value={formData.programFocus}
              onChange={(e) => setFormData({ ...formData, programFocus: e.target.value })}
              className="input-field"
            >
              <option>All Programs</option>
              <option>Project Family Build</option>
              <option>Responsible Fatherhood</option>
              <option>Celebration Events</option>
              <option>Louisiana Barracks</option>
            </select>
          </div>

          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-900">
              The AI will analyze the selected RFP and generate a structured plan with sections, word targets, and alignment scores.
            </p>
          </div>
        </div>
      </Modal>

      {/* Plan Detail Modal */}
      {selectedPlan && (
        <Modal
          open={showPlanDetail}
          onClose={() => setShowPlanDetail(false)}
          title={selectedPlan.name}
          size="2xl"
        >
          <div className="space-y-6">
            {/* Status & Actions */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div>
                <p className="text-sm text-gray-600">Current Status</p>
                <StatusIndicator status={statusConfig[selectedPlan.status]} size="md" />
              </div>
              <div className="flex gap-2">
                <select
                  value={selectedPlan.status}
                  onChange={(e) => handleUpdateStatus(selectedPlan.id, e.target.value)}
                  className="input-field"
                >
                  <option value="draft">Draft</option>
                  <option value="review">Review</option>
                  <option value="approved">Approved</option>
                  <option value="submitted">Submitted</option>
                </select>
              </div>
            </div>

            {/* Overall Progress */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Overall Progress</h4>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Content Written</span>
                    <span className="text-sm font-semibold text-gray-900">{selectedPlan.wordCount} / {selectedPlan.wordTarget} words</span>
                  </div>
                  <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-foam-primary rounded-full"
                      style={{ width: `${(selectedPlan.wordCount / selectedPlan.wordTarget) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Sections */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Sections</h4>
              <div className="space-y-3">
                {mockPlanSections.map((section) => (
                  <div key={section.id} className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-start gap-3 flex-1">
                        {section.complete ? (
                          <CheckCircle size={20} className="text-emerald-600 flex-shrink-0 mt-0.5" />
                        ) : (
                          <Circle size={20} className="text-gray-300 flex-shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{section.title}</p>
                          <div className="flex gap-4 mt-2 text-sm text-gray-600">
                            <span>{section.words} / {section.target} words</span>
                            <span>•</span>
                            <span>Alignment: {section.alignmentScore}%</span>
                          </div>
                        </div>
                      </div>
                      <button className="text-sm text-foam-primary hover:underline">Edit</button>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-foam-primary rounded-full"
                        style={{ width: `${(section.words / section.target) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Compliance Checklist */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Compliance Checklist</h4>
              <div className="space-y-2">
                {[
                  'All mandatory sections completed',
                  'Word counts within limits',
                  'Formatting requirements met',
                  'Required evidence included',
                  'Budget narrative justified',
                  'Evaluation plan detailed'
                ].map((item, index) => (
                  <label key={index} className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg cursor-pointer">
                    <input type="checkbox" className="rounded" defaultChecked={index < 3} />
                    <span className="text-sm text-gray-700">{item}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Export Options */}
            <div className="flex gap-2 pt-4 border-t border-gray-200">
              <button
                onClick={() => handleExportPlan(selectedPlan.id)}
                className="flex-1 btn-primary"
              >
                <Download size={20} />
                Export to DOCX
              </button>
              <button
                onClick={() => handlePrintPlan(selectedPlan.id)}
                className="flex-1 btn-secondary"
              >
                <Printer size={20} />
                Print Preview
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
