import { useState, useMemo, useEffect } from 'react'
import { Plus, Edit2, Trash2, Clock, Tag, Filter, Download, Upload as UploadIcon } from 'lucide-react'
import DataTable from '../components/common/DataTable'
import Modal from '../components/common/Modal'
import TagList from '../components/common/TagList'
import toast from 'react-hot-toast'
import { apiClient } from '../api/client'

const mockSections = [
  {
    id: 1,
    title: 'Organizational History and Mission',
    category: 'Basic Info',
    content: 'FOAM was founded in 2018 with the mission to strengthen fatherhood through mentorship, education, and community engagement.',
    tags: ['org_narrative', 'core_mission'],
    program: 'All Programs',
    lastUpdated: '2024-02-10',
    version: 5,
    evidenceType: 'Documented'
  },
  {
    id: 2,
    title: 'Project Family Build Program Overview',
    category: 'Program Specific',
    content: 'Project Family Build is FOAM\'s flagship initiative designed to strengthen the father-child relationship through structured workshops and mentorship.',
    tags: ['program_specific', 'family_services'],
    program: 'Project Family Build',
    lastUpdated: '2024-02-12',
    version: 8,
    evidenceType: 'Documented'
  },
  {
    id: 3,
    title: 'Responsible Fatherhood Classes Curriculum',
    category: 'Program Specific',
    content: 'Our curriculum covers communication skills, financial literacy, parenting best practices, and community involvement.',
    tags: ['program_specific', 'education', 'evidence_based'],
    program: 'Responsible Fatherhood',
    lastUpdated: '2024-02-08',
    version: 6,
    evidenceType: 'Evidence-Based'
  },
  {
    id: 4,
    title: 'Organizational Capacity and Infrastructure',
    category: 'Org Narrative',
    content: 'FOAM maintains state-of-the-art facilities in Baton Rouge with capacity to serve 500+ participants annually.',
    tags: ['capacity', 'infrastructure'],
    program: 'All Programs',
    lastUpdated: '2024-02-05',
    version: 4,
    evidenceType: 'Documented'
  },
  {
    id: 5,
    title: 'Evaluation and Outcomes Framework',
    category: 'Maintenance',
    content: 'Outcomes measured through pre/post assessments, participant satisfaction surveys, and 6-month follow-up evaluations.',
    tags: ['evaluation', 'outcomes'],
    program: 'All Programs',
    lastUpdated: '2024-02-11',
    version: 3,
    evidenceType: 'Documented'
  },
  {
    id: 6,
    title: 'Celebration of Fatherhood Events',
    category: 'Program Specific',
    content: 'Annual citywide celebration highlighting fatherhood role models, featuring awards, performances, and community activities.',
    tags: ['celebration', 'community_engagement'],
    program: 'Celebration Events',
    lastUpdated: '2024-02-09',
    version: 2,
    evidenceType: 'Documented'
  }
]

const categories = ['All', 'Basic Info', 'Org Narrative', 'Program Specific', 'Maintenance']
const programs = ['All Programs', 'Project Family Build', 'Responsible Fatherhood', 'Celebration Events', 'Louisiana Barracks']

export default function BoilerplateManager() {
  const [sections, setSections] = useState(mockSections)
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [selectedProgram, setSelectedProgram] = useState('All Programs')
  const [searchQuery, setSearchQuery] = useState('')
  const [editingSection, setEditingSection] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [viewingHistory, setViewingHistory] = useState(null)
  const [formData, setFormData] = useState({
    title: '',
    category: 'Basic Info',
    content: '',
    tags: [],
    program: 'All Programs',
    evidenceType: 'Documented'
  })

  // Fetch sections from API on mount
  useEffect(() => {
    async function fetchSections() {
      try {
        const res = await apiClient.getSections({ limit: 100 })
        const data = res.data
        const items = data.items || data.results || data
        if (Array.isArray(items) && items.length > 0) {
          setSections(items.map(s => ({
            id: s.id,
            title: s.title,
            category: s.category_name || s.category || 'Basic Info',
            content: s.content || '',
            tags: s.tags || [],
            program: s.program_area || s.program || 'All Programs',
            lastUpdated: s.updated_at ? s.updated_at.split('T')[0] : s.last_updated || '',
            version: s.version_number || s.version || 1,
            evidenceType: s.evidence_type || 'Documented'
          })))
        }
      } catch (err) {
        console.log('Boilerplate API unavailable, using mock data:', err.message)
      }
    }
    fetchSections()
  }, [])

  const filteredSections = useMemo(() => {
    return sections.filter((section) => {
      const matchCategory = selectedCategory === 'All' || section.category === selectedCategory
      const matchProgram = selectedProgram === 'All Programs' || section.program === selectedProgram
      const matchSearch = section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        section.content.toLowerCase().includes(searchQuery.toLowerCase())
      return matchCategory && matchProgram && matchSearch
    })
  }, [sections, selectedCategory, selectedProgram, searchQuery])

  const handleAddSection = () => {
    setEditingSection(null)
    setFormData({
      title: '',
      category: 'Basic Info',
      content: '',
      tags: [],
      program: 'All Programs',
      evidenceType: 'Documented'
    })
    setShowModal(true)
  }

  const handleEditSection = (section) => {
    setEditingSection(section)
    setFormData({
      title: section.title,
      category: section.category,
      content: section.content,
      tags: section.tags,
      program: section.program,
      evidenceType: section.evidenceType
    })
    setShowModal(true)
  }

  const handleSaveSection = async () => {
    if (!formData.title.trim() || !formData.content.trim()) {
      toast.error('Please fill in all required fields')
      return
    }

    try {
      if (editingSection) {
        await apiClient.updateSection(editingSection.id, {
          title: formData.title,
          content: formData.content,
          category_name: formData.category,
          program_area: formData.program,
          evidence_type: formData.evidenceType,
          tags: formData.tags
        })
        setSections(sections.map((s) =>
          s.id === editingSection.id
            ? { ...s, ...formData, version: s.version + 1, lastUpdated: new Date().toISOString().split('T')[0] }
            : s
        ))
        toast.success('Section updated successfully')
      } else {
        const res = await apiClient.createSection({
          title: formData.title,
          content: formData.content,
          category_name: formData.category,
          program_area: formData.program,
          evidence_type: formData.evidenceType,
          tags: formData.tags
        })
        const newSection = res.data
        setSections([
          {
            ...formData,
            id: newSection.id || Math.max(0, ...sections.map((s) => typeof s.id === 'number' ? s.id : 0)) + 1,
            lastUpdated: new Date().toISOString().split('T')[0],
            version: 1
          },
          ...sections
        ])
        toast.success('Section created successfully')
      }
    } catch (err) {
      console.log('API save failed, updating locally:', err.message)
      // Fallback: update local state even if API fails
      if (editingSection) {
        setSections(sections.map((s) =>
          s.id === editingSection.id
            ? { ...s, ...formData, version: s.version + 1, lastUpdated: new Date().toISOString().split('T')[0] }
            : s
        ))
        toast.success('Section updated locally')
      } else {
        setSections([
          {
            ...formData,
            id: Math.max(0, ...sections.map((s) => typeof s.id === 'number' ? s.id : 0)) + 1,
            lastUpdated: new Date().toISOString().split('T')[0],
            version: 1
          },
          ...sections
        ])
        toast.success('Section created locally')
      }
    }
    setShowModal(false)
  }

  const handleDeleteSection = async (id) => {
    try {
      await apiClient.deleteSection(id)
    } catch (err) {
      console.log('API delete failed, removing locally:', err.message)
    }
    setSections(sections.filter((s) => s.id !== id))
    toast.success('Section deleted')
  }

  const handleAddTag = (newTag) => {
    if (newTag && !formData.tags.includes(newTag)) {
      setFormData({ ...formData, tags: [...formData.tags, newTag] })
    }
  }

  const handleRemoveTag = (index) => {
    setFormData({ ...formData, tags: formData.tags.filter((_, i) => i !== index) })
  }

  const tableColumns = [
    {
      key: 'title',
      label: 'Section Title',
      sortable: true,
      render: (value, row) => (
        <div>
          <p className="font-semibold text-gray-900">{value}</p>
          <p className="text-xs text-gray-500 mt-1">{row.program}</p>
        </div>
      )
    },
    {
      key: 'category',
      label: 'Category',
      sortable: true,
      render: (value) => <span className="inline-block px-2 py-1 bg-blue-50 text-blue-800 text-xs font-medium rounded">{value}</span>
    },
    {
      key: 'evidenceType',
      label: 'Evidence',
      sortable: true,
      render: (value) => <span className="text-sm">{value}</span>
    },
    {
      key: 'tags',
      label: 'Tags',
      render: (value) => <TagList tags={value} />
    },
    {
      key: 'lastUpdated',
      label: 'Last Updated',
      sortable: true,
      render: (value) => <span className="text-sm text-gray-600">{value}</span>
    },
    {
      key: 'version',
      label: 'Version',
      sortable: true,
      render: (value) => <span className="font-medium text-gray-900">v{value}</span>
    },
    {
      key: 'id',
      label: 'Actions',
      render: (value, row) => (
        <div className="flex gap-2">
          <button
            onClick={() => setViewingHistory(row)}
            className="p-1 hover:bg-gray-100 rounded transition-colors text-gray-600"
            title="View History"
          >
            <Clock size={18} />
          </button>
          <button
            onClick={() => handleEditSection(row)}
            className="p-1 hover:bg-gray-100 rounded transition-colors text-gray-600"
            title="Edit"
          >
            <Edit2 size={18} />
          </button>
          <button
            onClick={() => handleDeleteSection(row.id)}
            className="p-1 hover:bg-gray-100 rounded transition-colors text-foam-red"
            title="Delete"
          >
            <Trash2 size={18} />
          </button>
        </div>
      )
    }
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="section-title">Boilerplate Manager</h2>
          <p className="text-gray-600 mt-2">Manage reusable content sections across all grant applications</p>
        </div>
        <button onClick={handleAddSection} className="btn-primary">
          <Plus size={20} />
          New Section
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="p-6 space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <Filter size={18} className="text-gray-600" />
            <span className="font-semibold text-gray-900">Filters & Search</span>
          </div>

          <input
            type="text"
            placeholder="Search sections by title or content..."
            className="input-field w-full"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">Category</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="input-field"
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">Program</label>
              <select
                value={selectedProgram}
                onChange={(e) => setSelectedProgram(e.target.value)}
                className="input-field"
              >
                {programs.map((prog) => (
                  <option key={prog} value={prog}>{prog}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button className="btn-secondary btn-sm">
              <Download size={16} />
              Export
            </button>
            <button className="btn-secondary btn-sm">
              <UploadIcon size={16} />
              Import
            </button>
          </div>
        </div>
      </div>

      {/* Sections Table */}
      <div className="card">
        <div className="p-6">
          <DataTable
            columns={tableColumns}
            data={filteredSections}
            searchable={false}
            pageSize={10}
          />
        </div>
      </div>

      {/* Edit Modal */}
      <Modal
        open={showModal}
        onClose={() => setShowModal(false)}
        title={editingSection ? 'Edit Section' : 'Create New Section'}
        size="lg"
        footer={
          <>
            <button onClick={() => setShowModal(false)} className="btn-secondary">
              Cancel
            </button>
            <button onClick={handleSaveSection} className="btn-primary">
              {editingSection ? 'Update' : 'Create'} Section
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Title</label>
            <input
              type="text"
              placeholder="Section title"
              className="input-field"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">Category</label>
              <select
                className="input-field"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              >
                {categories.filter((c) => c !== 'All').map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">Evidence Type</label>
              <select
                className="input-field"
                value={formData.evidenceType}
                onChange={(e) => setFormData({ ...formData, evidenceType: e.target.value })}
              >
                <option>Documented</option>
                <option>Evidence-Based</option>
                <option>Qualitative</option>
                <option>Mixed Methods</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Program</label>
            <select
              className="input-field"
              value={formData.program}
              onChange={(e) => setFormData({ ...formData, program: e.target.value })}
            >
              {programs.map((prog) => (
                <option key={prog} value={prog}>{prog}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Content</label>
            <textarea
              placeholder="Section content..."
              className="input-field min-h-[200px]"
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Tags</label>
            <div className="flex gap-2 mb-3">
              {formData.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded cursor-pointer hover:bg-blue-200"
                  onClick={() => handleRemoveTag(index)}
                >
                  {tag} ×
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Add tag..."
                className="input-field flex-1"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAddTag(e.target.value)
                    e.target.value = ''
                  }
                }}
              />
            </div>
          </div>
        </div>
      </Modal>

      {/* History Modal */}
      {viewingHistory && (
        <Modal
          open={!!viewingHistory}
          onClose={() => setViewingHistory(null)}
          title={`Version History: ${viewingHistory.title}`}
          size="lg"
        >
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="font-semibold text-blue-900">Current Version: v{viewingHistory.version}</p>
              <p className="text-sm text-blue-700 mt-2">Last updated: {viewingHistory.lastUpdated}</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Version History</h4>
              <div className="space-y-2">
                {[...Array(viewingHistory.version)].map((_, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded border border-gray-200">
                    <div>
                      <p className="font-medium text-gray-900">v{viewingHistory.version - i}</p>
                      <p className="text-xs text-gray-500">Updated {Math.floor(i * 1.5) || 'today'} days ago</p>
                    </div>
                    <button className="text-sm text-foam-primary hover:underline">View Diff</button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
