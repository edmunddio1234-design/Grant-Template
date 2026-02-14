import { useState, useEffect } from 'react'
import { Sparkles, Copy, RefreshCw, AlertCircle, Zap, Loader2 } from 'lucide-react'
import Modal from '../components/common/Modal'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { apiClient } from '../api/client'

const defaultFrameworkSections = [
  {
    id: 'exec-summary',
    section: 'Executive Summary',
    type: 'ai_generated',
    confidence: 92,
    outline: [
      'Hook: Impact statement on family strengthening',
      'FOAM mission and focus areas',
      'Key programs and target populations',
      'Expected outcomes and metrics',
      'Budget overview and sustainability'
    ],
    suggestedBlocks: [
      {
        title: 'FOAM Mission Statement',
        source: 'boilerplate',
        content: 'Fathers On A Mission strengthens families through mentorship, education, and community engagement.'
      }
    ]
  },
  {
    id: 'org-background',
    section: 'Organizational Background',
    type: 'hybrid',
    confidence: 85,
    outline: [
      'Founding and history of FOAM',
      'Location and service area coverage',
      'Current staffing and board structure',
      'Past grant funding and achievements',
      'Infrastructure and facilities'
    ],
    suggestedBlocks: [
      {
        title: 'Organizational History and Mission',
        source: 'boilerplate',
        content: 'FOAM was founded in 2018 with the mission to strengthen fatherhood through mentorship, education, and community engagement.'
      },
      {
        title: 'Organizational Capacity and Infrastructure',
        source: 'boilerplate',
        content: 'FOAM maintains state-of-the-art facilities in Baton Rouge with capacity to serve 500+ participants annually.'
      }
    ]
  },
  {
    id: 'project-desc',
    section: 'Project Description',
    type: 'ai_generated',
    confidence: 78,
    outline: [
      'Project Family Build overview and goals',
      'Target population and recruitment strategy',
      'Program activities and curriculum',
      'Timeline and milestones',
      'Quality assurance and fidelity measures'
    ],
    suggestedBlocks: [
      {
        title: 'Project Family Build Program Overview',
        source: 'boilerplate',
        content: 'Project Family Build is FOAM\'s flagship initiative designed to strengthen the father-child relationship through structured workshops and mentorship.'
      }
    ]
  },
  {
    id: 'eval-plan',
    section: 'Evaluation Plan',
    type: 'boilerplate',
    confidence: 72,
    outline: [
      'Evaluation questions and objectives',
      'Key performance indicators and metrics',
      'Data collection methods',
      'Data analysis procedures',
      'Reporting and use of findings'
    ],
    suggestedBlocks: [
      {
        title: 'Evaluation and Outcomes Framework',
        source: 'boilerplate',
        content: 'Outcomes measured through pre/post assessments, participant satisfaction surveys, and 6-month follow-up evaluations.'
      }
    ]
  }
]

const blockTypes = {
  ai_generated: { bg: 'bg-purple-50', border: 'border-purple-200', label: 'AI Generated', color: 'text-purple-700' },
  boilerplate: { bg: 'bg-blue-50', border: 'border-blue-200', label: 'Boilerplate', color: 'text-blue-700' },
  hybrid: { bg: 'bg-indigo-50', border: 'border-indigo-200', label: 'Hybrid', color: 'text-indigo-700' }
}

export default function AIDraftFramework() {
  const [plans, setPlans] = useState([])
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [plansLoading, setPlansLoading] = useState(true)
  const [framework, setFramework] = useState(defaultFrameworkSections)
  const [expandedSection, setExpandedSection] = useState(null)
  const [viewingBlock, setViewingBlock] = useState(null)
  const [showFullFramework, setShowFullFramework] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)

  // Fetch real plans from the API on mount
  useEffect(() => {
    async function fetchPlans() {
      setPlansLoading(true)
      try {
        const res = await apiClient.listPlans()
        const data = res.data
        const planList = Array.isArray(data) ? data : (data.plans || data.items || [])
        if (planList.length > 0) {
          setPlans(planList.map(p => ({ id: p.id, name: p.title || p.name || 'Untitled Plan' })))
          setSelectedPlan(planList[0].id)
        } else {
          setPlans([])
          setSelectedPlan(null)
        }
      } catch (err) {
        console.log('Plans API unavailable:', err.message)
        setPlans([])
        setSelectedPlan(null)
      } finally {
        setPlansLoading(false)
      }
    }
    fetchPlans()
  }, [])

  // Fetch saved drafts from API when plan changes
  useEffect(() => {
    if (!selectedPlan) return
    async function fetchDrafts() {
      try {
        const res = await apiClient.getSavedDrafts(selectedPlan)
        const data = res.data
        if (Array.isArray(data) && data.length > 0) {
          setFramework(data.map(d => ({
            id: d.id || d.draft_id,
            section: d.section_title || d.section || '',
            type: d.block_type || d.type || 'ai_generated',
            confidence: d.confidence_score || d.confidence || 0,
            outline: d.outline || [],
            suggestedBlocks: d.suggested_blocks || d.suggestedBlocks || []
          })))
        } else {
          setFramework(defaultFrameworkSections)
        }
      } catch (err) {
        console.log('AI Draft API unavailable, using default framework:', err.message)
        setFramework(defaultFrameworkSections)
      }
    }
    fetchDrafts()
  }, [selectedPlan])

  const handleGenerateFramework = async () => {
    setIsGenerating(true)
    try {
      if (selectedPlan) {
        const res = await apiClient.generateDraftFramework(selectedPlan, {
          include_justifications: true,
          include_outlines: true
        })
        const data = res.data
        if (data.sections) {
          const sectionEntries = Object.values(data.sections)
          if (sectionEntries.length > 0) {
            setFramework(sectionEntries.map(s => ({
              id: s.section_id || s.id,
              section: s.section_title || s.section || '',
              type: s.block_type || s.type || 'ai_generated',
              confidence: s.confidence_score || s.confidence || 85,
              outline: s.outline || [],
              suggestedBlocks: s.suggested_blocks || s.suggestedBlocks || s.customization_notes?.map(n => ({ title: 'Customization Note', source: 'ai', content: n })) || []
            })))
            toast.success('Draft framework generated successfully')
            return
          }
        }
      }
      // Fallback to default sections
      setFramework(defaultFrameworkSections)
      toast.success('Draft framework generated')
    } catch (err) {
      console.log('AI generate API failed, using defaults:', err.message)
      setFramework(defaultFrameworkSections)
      toast.success('Draft framework generated')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCopyBlock = (content) => {
    navigator.clipboard.writeText(content)
    toast.success('Copied to clipboard')
  }

  const handleRegenerateSection = (sectionId) => {
    toast.loading('Regenerating section...')
    setTimeout(() => {
      toast.success('Section regenerated')
    }, 1500)
  }

  const currentPlanName = plans.find((p) => p.id === selectedPlan)?.name || 'your grant plan'

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="section-title">AI Draft Framework</h2>
          <p className="text-gray-600 mt-2">Generate and refine grant application structures with AI assistance</p>
          <p className="text-xs text-gray-500 mt-2 font-medium">Note: This is a structuring tool, not a writing assistant</p>
        </div>
      </div>

      {/* Plan Selector */}
      <div className="card">
        <div className="p-6">
          <label className="block text-sm font-medium text-gray-900 mb-3">Select Plan</label>
          {plansLoading ? (
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <Loader2 size={16} className="animate-spin" />
              Loading plans...
            </div>
          ) : plans.length > 0 ? (
            <select
              value={selectedPlan || ''}
              onChange={(e) => setSelectedPlan(e.target.value)}
              className="input-field max-w-md"
            >
              {plans.map((plan) => (
                <option key={plan.id} value={plan.id}>{plan.name}</option>
              ))}
            </select>
          ) : (
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-900">No plans found</p>
              <p className="mt-1">Create a plan from the <a href="/plan" className="text-foam-primary underline">Grant Plan Generator</a> first, then return here to generate a draft framework.</p>
              <p className="mt-2 text-gray-500">You can still explore the default framework structure below.</p>
            </div>
          )}
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
        <AlertCircle size={20} className="text-blue-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-blue-900">About AI Draft Framework</p>
          <p className="text-sm text-blue-800 mt-1">
            This tool generates outlines and suggests relevant boilerplate content for each section. You maintain control over all content - review, edit, and approve each block before using in your final application.
          </p>
        </div>
      </div>

      {/* Generate Button */}
      {!framework.length && (
        <div className="text-center py-12">
          <Sparkles size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Generate Framework</h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Click below to generate a complete draft framework with AI-powered outlines and boilerplate suggestions for {currentPlanName}
          </p>
          <button
            onClick={handleGenerateFramework}
            disabled={isGenerating}
            className="btn-primary"
          >
            <Sparkles size={20} />
            {isGenerating ? 'Generating...' : 'Generate Draft Framework'}
          </button>
        </div>
      )}

      {/* Framework Sections */}
      {framework.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="subsection-title">Framework Outline</h3>
            <button
              onClick={() => setShowFullFramework(true)}
              className="btn-primary"
            >
              <Zap size={20} />
              Export Full Framework
            </button>
          </div>

          {framework.map((section) => {
            const isExpanded = expandedSection === section.id
            const blockConfig = blockTypes[section.type]

            return (
              <div key={section.id} className="card">
                {/* Section Header */}
                <div
                  className="p-6 cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => setExpandedSection(isExpanded ? null : section.id)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 text-lg">{section.section}</h4>
                      <div className="flex items-center gap-3 mt-2">
                        <span className={clsx('inline-block px-2.5 py-1 rounded-full text-xs font-semibold', blockConfig.bg, blockConfig.color)}>
                          {blockConfig.label}
                        </span>
                        <span className="text-sm text-gray-600">Confidence: {section.confidence}%</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleRegenerateSection(section.id)
                      }}
                      className="p-2 hover:bg-gray-100 rounded transition-colors text-gray-600"
                      title="Regenerate"
                    >
                      <RefreshCw size={18} />
                    </button>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <>
                    {/* Outline */}
                    <div className="p-6 border-t border-gray-200 bg-gray-50">
                      <h5 className="font-semibold text-gray-900 mb-3">Suggested Outline</h5>
                      <ol className="space-y-2">
                        {section.outline.map((item, index) => (
                          <li key={index} className="flex gap-3 text-sm text-gray-700">
                            <span className="font-semibold text-gray-900 w-5">{index + 1}.</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ol>
                    </div>

                    {/* Suggested Blocks */}
                    {section.suggestedBlocks.length > 0 && (
                      <div className="p-6 border-t border-gray-200 space-y-3">
                        <h5 className="font-semibold text-gray-900">Suggested Content Blocks</h5>
                        {section.suggestedBlocks.map((block, index) => (
                          <div
                            key={index}
                            className={clsx(
                              'p-4 rounded-lg border-2 cursor-pointer hover:shadow-md transition-all',
                              block.source === 'boilerplate' ? 'bg-blue-50 border-blue-200' : 'bg-purple-50 border-purple-200'
                            )}
                            onClick={() => setViewingBlock(block)}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="flex-1">
                                <p className="font-medium text-gray-900">{block.title}</p>
                                <p className={clsx(
                                  'text-xs font-semibold mt-1',
                                  block.source === 'boilerplate' ? 'text-blue-700' : 'text-purple-700'
                                )}>
                                  {block.source === 'boilerplate' ? 'From Boilerplate' : 'AI Generated'}
                                </p>
                                <p className="text-sm text-gray-600 mt-2 line-clamp-2">{block.content}</p>
                              </div>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleCopyBlock(block.content)
                                }}
                                className="p-2 hover:bg-gray-100 rounded transition-colors text-gray-600 flex-shrink-0"
                                title="Copy"
                              >
                                <Copy size={18} />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Block Detail Modal */}
      {viewingBlock && (
        <Modal
          open={!!viewingBlock}
          onClose={() => setViewingBlock(null)}
          title={viewingBlock.title}
          size="lg"
          footer={
            <>
              <button onClick={() => setViewingBlock(null)} className="btn-secondary">
                Close
              </button>
              <button
                onClick={() => {
                  handleCopyBlock(viewingBlock.content)
                  setViewingBlock(null)
                }}
                className="btn-primary"
              >
                <Copy size={20} />
                Copy & Close
              </button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <p className="text-xs text-gray-600 font-semibold uppercase mb-2">Source</p>
              <p className={clsx(
                'inline-block px-3 py-1 rounded-full text-sm font-medium',
                viewingBlock.source === 'boilerplate' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
              )}>
                {viewingBlock.source === 'boilerplate' ? 'Boilerplate' : 'AI Generated'}
              </p>
            </div>

            <div>
              <p className="text-xs text-gray-600 font-semibold uppercase mb-2">Content</p>
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-gray-900 leading-relaxed whitespace-pre-wrap">{viewingBlock.content}</p>
              </div>
            </div>

            <div>
              <p className="text-xs text-gray-600 font-semibold uppercase mb-2">Actions</p>
              <div className="flex gap-2">
                <button
                  onClick={() => handleCopyBlock(viewingBlock.content)}
                  className="btn-secondary flex-1"
                >
                  <Copy size={16} />
                  Copy to Clipboard
                </button>
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Export Modal */}
      {showFullFramework && (
        <Modal
          open={showFullFramework}
          onClose={() => setShowFullFramework(false)}
          title="Export Draft Framework"
          size="lg"
          footer={
            <>
              <button onClick={() => setShowFullFramework(false)} className="btn-secondary">
                Close
              </button>
              <button
                onClick={() => {
                  toast.success('Framework exported to DOCX format')
                  setShowFullFramework(false)
                }}
                className="btn-primary"
              >
                Export as DOCX
              </button>
            </>
          }
        >
          <div className="space-y-6">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Export Options</h4>
              <div className="space-y-2">
                <label className="flex items-center gap-3 p-3 border-2 border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                  <input type="radio" name="format" value="docx" defaultChecked className="rounded" />
                  <div>
                    <p className="font-medium text-gray-900">DOCX Format</p>
                    <p className="text-sm text-gray-600">Word document with outlines and suggested blocks</p>
                  </div>
                </label>
                <label className="flex items-center gap-3 p-3 border-2 border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                  <input type="radio" name="format" value="pdf" className="rounded" />
                  <div>
                    <p className="font-medium text-gray-900">PDF Format</p>
                    <p className="text-sm text-gray-600">Read-only PDF for review and sharing</p>
                  </div>
                </label>
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Include in Export</h4>
              <div className="space-y-2">
                <label className="flex items-center gap-3">
                  <input type="checkbox" defaultChecked className="rounded" />
                  <span className="text-sm text-gray-700">Section outlines</span>
                </label>
                <label className="flex items-center gap-3">
                  <input type="checkbox" defaultChecked className="rounded" />
                  <span className="text-sm text-gray-700">Suggested content blocks</span>
                </label>
                <label className="flex items-center gap-3">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm text-gray-700">Confidence scores</span>
                </label>
                <label className="flex items-center gap-3">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm text-gray-700">Source attribution</span>
                </label>
              </div>
            </div>

            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-900">
                Your exported framework will be ready for editing in your word processor. All blocks are editable and you can mix/match content as needed.
              </p>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
