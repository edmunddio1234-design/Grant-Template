import { useState, useEffect } from 'react'
import { Sparkles, Copy, RefreshCw, AlertCircle, Loader2, ChevronDown, ChevronUp, FileText, Edit3, Check, X } from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { apiClient } from '../api/client'

export default function AIDraftFramework() {
  const [plans, setPlans] = useState([])
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [plansLoading, setPlansLoading] = useState(true)
  const [sections, setSections] = useState([])
  const [expandedSection, setExpandedSection] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatingSection, setGeneratingSection] = useState(null)
  const [editingSection, setEditingSection] = useState(null)
  const [editContent, setEditContent] = useState('')

  // Fetch plans on mount
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
        }
      } catch (err) {
        console.log('Plans API unavailable:', err.message)
      } finally {
        setPlansLoading(false)
      }
    }
    fetchPlans()
  }, [])

  // Generate full draft framework
  const handleGenerateAll = async () => {
    if (!selectedPlan) {
      toast.error('Please select a plan first')
      return
    }
    setIsGenerating(true)
    setSections([])
    try {
      const res = await apiClient.generateDraftFramework(selectedPlan, {
        include_justifications: true,
        include_outlines: true
      })
      const data = res.data
      if (data.sections) {
        const sectionEntries = Object.values(data.sections)
        if (sectionEntries.length > 0) {
          const mapped = sectionEntries.map(s => ({
            id: s.section_id || s.id,
            title: s.section_title || '',
            order: s.section_order || 0,
            wordLimit: s.word_limit || 500,
            content: s.suggested_content || '',
            outline: s.outline || [],
            alignmentNotes: s.alignment_notes || [],
            customizationNotes: s.customization_notes || [],
            source: s.source || 'ai_generated',
            model: s.model || null
          }))
          mapped.sort((a, b) => a.order - b.order)
          setSections(mapped)
          setExpandedSection(mapped[0]?.id)

          // Check if AI actually worked or returned placeholders
          const config = data.generation_config || {}
          if (config.placeholder_count > 0 && config.ai_error) {
            toast.error(`AI error: ${config.ai_error}`, { duration: 8000 })
          } else if (config.placeholder_count > 0) {
            toast.error('AI service unavailable — showing placeholder content. Check API key.', { duration: 6000 })
          } else {
            toast.success(`Draft generated with ${mapped.length} sections`)
          }
          return
        }
      }
      toast.error('No sections returned from API')
    } catch (err) {
      console.error('Generate failed:', err)
      toast.error('Failed to generate draft — check that a plan with sections exists')
    } finally {
      setIsGenerating(false)
    }
  }

  // Regenerate a single section
  const handleRegenerateSection = async (sectionId) => {
    if (!selectedPlan) return
    setGeneratingSection(sectionId)
    try {
      const section = sections.find(s => s.id === sectionId)
      const res = await apiClient.generateInsertBlock({
        plan_id: selectedPlan,
        section_id: sectionId,
        context: `Generate a complete draft for the "${section?.title}" section of this grant application. Include specific details about FOAM's programs, capacity, and outcomes.`,
        style: 'formal',
        length: 'long'
      })
      const data = res.data
      if (data.generated_content) {
        setSections(prev => prev.map(s =>
          s.id === sectionId
            ? { ...s, content: data.generated_content, source: data.metadata?.source || 'ai_generated' }
            : s
        ))
        toast.success(`"${section?.title}" regenerated`)
      }
    } catch (err) {
      console.error('Regenerate failed:', err)
      toast.error('Failed to regenerate section')
    } finally {
      setGeneratingSection(null)
    }
  }

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const handleCopyAll = () => {
    const fullText = sections.map(s => `## ${s.title}\n\n${s.content}`).join('\n\n---\n\n')
    navigator.clipboard.writeText(fullText)
    toast.success('Full draft copied to clipboard')
  }

  const handleSaveEdit = (sectionId) => {
    setSections(prev => prev.map(s =>
      s.id === sectionId ? { ...s, content: editContent } : s
    ))
    setEditingSection(null)
    setEditContent('')
    toast.success('Section updated')
  }

  const currentPlanName = plans.find(p => p.id === selectedPlan)?.name || 'your grant plan'

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="section-title">AI Draft Framework</h2>
          <p className="text-gray-600 mt-2">Generate real grant application draft text with AI</p>
        </div>
        {sections.length > 0 && (
          <button onClick={handleCopyAll} className="btn-secondary">
            <Copy size={18} />
            Copy Full Draft
          </button>
        )}
      </div>

      {/* Plan Selector + Generate */}
      <div className="card">
        <div className="p-6">
          <label className="block text-sm font-medium text-gray-900 mb-3">Select Plan</label>
          {plansLoading ? (
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <Loader2 size={16} className="animate-spin" />
              Loading plans...
            </div>
          ) : plans.length > 0 ? (
            <div className="flex items-end gap-4">
              <div className="flex-1 max-w-md">
                <select
                  value={selectedPlan || ''}
                  onChange={(e) => {
                    setSelectedPlan(e.target.value)
                    setSections([])
                  }}
                  className="input-field"
                >
                  {plans.map(plan => (
                    <option key={plan.id} value={plan.id}>{plan.name}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleGenerateAll}
                disabled={isGenerating || !selectedPlan}
                className="btn-primary"
              >
                {isGenerating ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Generating Draft...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Generate AI Draft
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-900">No plans found</p>
              <p className="mt-1">Create a plan from the <a href="/plan" className="text-foam-primary underline">Grant Plan Generator</a> first, then return here to generate a draft.</p>
            </div>
          )}
        </div>
      </div>

      {/* Empty State */}
      {!isGenerating && sections.length === 0 && plans.length > 0 && (
        <div className="text-center py-16">
          <FileText size={56} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Draft Generated Yet</h3>
          <p className="text-gray-600 mb-6 max-w-lg mx-auto">
            Select a plan above and click <strong>"Generate AI Draft"</strong> to create a full grant application draft with real content for each section.
          </p>
        </div>
      )}

      {/* Loading State */}
      {isGenerating && (
        <div className="text-center py-16">
          <Loader2 size={48} className="mx-auto text-foam-primary mb-4 animate-spin" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Generating Draft for {currentPlanName}</h3>
          <p className="text-gray-600">AI is writing content for each section. This may take a moment...</p>
        </div>
      )}

      {/* Generated Sections */}
      {sections.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="subsection-title">
              Draft Sections ({sections.length})
            </h3>
            <button
              onClick={handleGenerateAll}
              disabled={isGenerating}
              className="btn-secondary btn-sm"
            >
              <RefreshCw size={16} />
              Regenerate All
            </button>
          </div>

          {sections.map((section) => {
            const isExpanded = expandedSection === section.id
            const isEditing = editingSection === section.id
            const isRegenerating = generatingSection === section.id
            const wordCount = section.content ? section.content.split(/\s+/).filter(Boolean).length : 0

            return (
              <div key={section.id} className="card overflow-hidden">
                {/* Section Header */}
                <div
                  className="p-5 cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => setExpandedSection(isExpanded ? null : section.id)}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 flex-1">
                      {isExpanded ? <ChevronUp size={20} className="text-gray-400" /> : <ChevronDown size={20} className="text-gray-400" />}
                      <div>
                        <h4 className="font-semibold text-gray-900 text-lg">{section.title}</h4>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-sm text-gray-500">{wordCount} words</span>
                          {section.wordLimit > 0 && (
                            <span className="text-sm text-gray-400">/ {section.wordLimit} target</span>
                          )}
                          <span className={clsx(
                            'inline-block px-2 py-0.5 rounded-full text-xs font-semibold',
                            section.source === 'ai_generated' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'
                          )}>
                            {section.source === 'ai_generated' ? 'AI Generated' : section.source === 'placeholder' ? 'Needs AI Key' : 'Draft'}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleCopy(section.content)}
                        className="p-2 hover:bg-gray-100 rounded transition-colors text-gray-500"
                        title="Copy section"
                      >
                        <Copy size={16} />
                      </button>
                      <button
                        onClick={() => {
                          setEditingSection(section.id)
                          setEditContent(section.content)
                          setExpandedSection(section.id)
                        }}
                        className="p-2 hover:bg-gray-100 rounded transition-colors text-gray-500"
                        title="Edit section"
                      >
                        <Edit3 size={16} />
                      </button>
                      <button
                        onClick={() => handleRegenerateSection(section.id)}
                        disabled={isRegenerating}
                        className="p-2 hover:bg-gray-100 rounded transition-colors text-gray-500"
                        title="Regenerate section"
                      >
                        {isRegenerating ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="border-t border-gray-200">
                    {/* Main Content */}
                    <div className="p-6">
                      {isEditing ? (
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <h5 className="font-semibold text-gray-900 text-sm">Editing: {section.title}</h5>
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleSaveEdit(section.id)}
                                className="btn-primary btn-sm"
                              >
                                <Check size={14} />
                                Save
                              </button>
                              <button
                                onClick={() => { setEditingSection(null); setEditContent('') }}
                                className="btn-secondary btn-sm"
                              >
                                <X size={14} />
                                Cancel
                              </button>
                            </div>
                          </div>
                          <textarea
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                            className="w-full h-64 p-4 border border-gray-300 rounded-lg text-sm leading-relaxed focus:ring-2 focus:ring-foam-primary focus:border-foam-primary resize-y"
                          />
                          <p className="text-xs text-gray-500">{editContent.split(/\s+/).filter(Boolean).length} words</p>
                        </div>
                      ) : isRegenerating ? (
                        <div className="flex items-center justify-center py-12">
                          <Loader2 size={32} className="text-foam-primary animate-spin" />
                          <span className="ml-3 text-gray-600">Regenerating content...</span>
                        </div>
                      ) : section.content ? (
                        <div className="prose max-w-none">
                          <div className="text-gray-800 leading-relaxed whitespace-pre-wrap text-sm">
                            {section.content}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-8 text-gray-400">
                          <p>No content generated yet. Click the regenerate button to generate content for this section.</p>
                        </div>
                      )}
                    </div>

                    {/* Outline & Notes */}
                    {(section.outline.length > 0 || section.alignmentNotes?.length > 0) && (
                      <div className="p-6 bg-gray-50 border-t border-gray-200">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {section.outline.length > 0 && (
                            <div>
                              <h5 className="font-semibold text-gray-900 text-sm mb-2">Outline</h5>
                              <ol className="space-y-1">
                                {section.outline.map((item, i) => (
                                  <li key={i} className="text-xs text-gray-600 flex gap-2">
                                    <span className="font-medium text-gray-500 w-4">{i + 1}.</span>
                                    <span>{item}</span>
                                  </li>
                                ))}
                              </ol>
                            </div>
                          )}
                          {section.alignmentNotes?.length > 0 && (
                            <div>
                              <h5 className="font-semibold text-gray-900 text-sm mb-2">Alignment Notes</h5>
                              <ul className="space-y-1">
                                {section.alignmentNotes.map((note, i) => (
                                  <li key={i} className="text-xs text-gray-600 flex gap-2">
                                    <span className="text-emerald-500">•</span>
                                    <span>{note}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Info Banner */}
      {sections.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
          <AlertCircle size={20} className="text-blue-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-blue-800">
            Review and edit each section before using in your final application. Click the edit icon to modify content, or copy individual sections or the full draft.
          </p>
        </div>
      )}
    </div>
  )
}
