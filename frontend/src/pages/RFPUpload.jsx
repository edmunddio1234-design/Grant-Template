import { useState } from 'react'
import { Trash2, Eye, Download, RefreshCw } from 'lucide-react'
import FileUpload from '../components/common/FileUpload'
import Modal from '../components/common/Modal'
import StatusIndicator from '../components/common/StatusIndicator'
import DataTable from '../components/common/DataTable'
import toast from 'react-hot-toast'

const mockRFPs = [
  {
    id: 1,
    name: 'Community Foundation Grant 2024',
    uploadDate: '2024-02-10',
    status: 'parsed',
    file: 'community_foundation_2024.pdf',
    requirements: 23,
    sections: 8,
    wordLimit: 5000
  },
  {
    id: 2,
    name: 'Department of Family Services RFP',
    uploadDate: '2024-02-08',
    status: 'analyzing',
    file: 'dfs_rfp_2024.docx',
    requirements: 31,
    sections: 12,
    wordLimit: 7500
  },
  {
    id: 3,
    name: 'Local Nonprofit Partnership Grant',
    uploadDate: '2024-02-05',
    status: 'uploaded',
    file: 'nonprofit_partnership.pdf',
    requirements: 18,
    sections: 6,
    wordLimit: 4000
  }
]

const mockRequirements = [
  { section: 'Executive Summary', requirements: 4, wordLimit: 250, mandatory: true },
  { section: 'Organizational Background', requirements: 3, wordLimit: 500, mandatory: true },
  { section: 'Project Description', requirements: 6, wordLimit: 1500, mandatory: true },
  { section: 'Evaluation Plan', requirements: 3, wordLimit: 750, mandatory: true },
  { section: 'Budget Narrative', requirements: 4, wordLimit: 400, mandatory: true },
  { section: 'Sustainability Plan', requirements: 2, wordLimit: 300, mandatory: false }
]

export default function RFPUpload() {
  const [rfps, setRFPs] = useState(mockRFPs)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [viewingRFP, setViewingRFP] = useState(null)
  const [showRequirements, setShowRequirements] = useState(false)

  const handleFileDrop = (files) => {
    setIsUploading(true)
    setTimeout(() => {
      setUploadedFiles([...uploadedFiles, ...files])
      setIsUploading(false)
      toast.success(`${files.length} file(s) uploaded successfully`)
    }, 2000)
  }

  const handleRemoveFile = (index) => {
    setUploadedFiles(uploadedFiles.filter((_, i) => i !== index))
  }

  const handleProcessRFP = (file) => {
    const newRFP = {
      id: Math.max(...rfps.map((r) => r.id)) + 1,
      name: file.name.replace(/\.[^/.]+$/, ''),
      uploadDate: new Date().toISOString().split('T')[0],
      status: 'parsing',
      file: file.name,
      requirements: Math.floor(Math.random() * 15) + 15,
      sections: Math.floor(Math.random() * 8) + 5,
      wordLimit: Math.floor(Math.random() * 3000) + 3000
    }
    setRFPs([newRFP, ...rfps])
    setUploadedFiles(uploadedFiles.filter((f) => f.name !== file.name))
    toast.success('RFP queued for parsing')
  }

  const handleDeleteRFP = (id) => {
    setRFPs(rfps.filter((r) => r.id !== id))
    toast.success('RFP deleted')
  }

  const statusConfig = {
    uploaded: 'pending',
    parsing: 'loading',
    parsed: 'active',
    analyzing: 'loading',
    analyzed: 'active',
    archived: 'error'
  }

  const tableColumns = [
    {
      key: 'name',
      label: 'RFP Name',
      sortable: true,
      render: (value, row) => (
        <div>
          <p className="font-semibold text-gray-900">{value}</p>
          <p className="text-xs text-gray-500 mt-1">{row.file}</p>
        </div>
      )
    },
    {
      key: 'uploadDate',
      label: 'Upload Date',
      sortable: true,
      render: (value) => <span className="text-sm text-gray-600">{value}</span>
    },
    {
      key: 'status',
      label: 'Status',
      sortable: true,
      render: (value) => (
        <StatusIndicator status={statusConfig[value]} size="sm" />
      )
    },
    {
      key: 'requirements',
      label: 'Requirements',
      sortable: true,
      render: (value) => <span className="font-medium text-gray-900">{value}</span>
    },
    {
      key: 'sections',
      label: 'Sections',
      sortable: true,
      render: (value) => <span className="text-gray-600">{value}</span>
    },
    {
      key: 'wordLimit',
      label: 'Total Words',
      sortable: true,
      render: (value) => <span className="text-gray-600">{value.toLocaleString()}</span>
    },
    {
      key: 'id',
      label: 'Actions',
      render: (value, row) => (
        <div className="flex gap-2">
          <button
            onClick={() => {
              setViewingRFP(row)
              setShowRequirements(true)
            }}
            className="p-1 hover:bg-gray-100 rounded transition-colors text-gray-600"
            title="View"
          >
            <Eye size={18} />
          </button>
          {row.status === 'parsed' || row.status === 'analyzed' ? (
            <button
              onClick={() => toast.success('Downloading RFP analysis')}
              className="p-1 hover:bg-gray-100 rounded transition-colors text-gray-600"
              title="Download"
            >
              <Download size={18} />
            </button>
          ) : (
            <button
              onClick={() => {
                const updated = rfps.map((r) =>
                  r.id === row.id ? { ...r, status: 'parsing' } : r
                )
                setRFPs(updated)
                toast.success('Re-parsing initiated')
              }}
              className="p-1 hover:bg-gray-100 rounded transition-colors text-gray-600"
              title="Re-parse"
            >
              <RefreshCw size={18} />
            </button>
          )}
          <button
            onClick={() => handleDeleteRFP(row.id)}
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
      <div>
        <h2 className="section-title">RFP Upload & Parse</h2>
        <p className="text-gray-600 mt-2">Upload grant RFPs and parse requirements automatically</p>
      </div>

      {/* Upload Section */}
      <div className="card">
        <div className="p-6">
          <h3 className="subsection-title mb-4">Upload New RFP</h3>
          <FileUpload
            onDrop={handleFileDrop}
            files={uploadedFiles}
            onRemove={handleRemoveFile}
            loading={isUploading}
          />

          {uploadedFiles.length > 0 && (
            <div className="mt-6 space-y-3">
              <h4 className="font-semibold text-gray-900">Ready to Process</h4>
              {uploadedFiles.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500 mt-1">{(file.size / 1024).toFixed(2)} KB</p>
                  </div>
                  <button
                    onClick={() => handleProcessRFP(file)}
                    className="btn-primary btn-sm"
                  >
                    Process
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* RFPs List */}
      <div className="card">
        <div className="p-6 border-b border-gray-200">
          <h3 className="subsection-title">Uploaded RFPs</h3>
          <p className="text-sm text-gray-600 mt-1">{rfps.length} RFP(s) in system</p>
        </div>
        <div className="p-6">
          <DataTable
            columns={tableColumns}
            data={rfps}
            searchable={true}
            searchFields={['name', 'file']}
            pageSize={10}
          />
        </div>
      </div>

      {/* Requirements Modal */}
      {viewingRFP && (
        <Modal
          open={showRequirements}
          onClose={() => setShowRequirements(false)}
          title={`RFP Details: ${viewingRFP.name}`}
          size="2xl"
        >
          <div className="space-y-6">
            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-600 font-semibold uppercase">Total Requirements</p>
                <p className="text-2xl font-bold text-blue-900 mt-2">{viewingRFP.requirements}</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-xs text-green-600 font-semibold uppercase">Sections</p>
                <p className="text-2xl font-bold text-green-900 mt-2">{viewingRFP.sections}</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <p className="text-xs text-purple-600 font-semibold uppercase">Total Word Limit</p>
                <p className="text-2xl font-bold text-purple-900 mt-2">{viewingRFP.wordLimit.toLocaleString()}</p>
              </div>
              <div className="p-4 bg-amber-50 rounded-lg">
                <p className="text-xs text-amber-600 font-semibold uppercase">Status</p>
                <p className="text-sm font-bold text-amber-900 mt-2">
                  <StatusIndicator status={statusConfig[viewingRFP.status]} size="sm" showBg={false} />
                </p>
              </div>
            </div>

            {/* Requirements Table */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Section Requirements</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 border-gray-200 bg-gray-50">
                      <th className="text-left py-2 px-3 font-semibold text-gray-900">Section</th>
                      <th className="text-center py-2 px-3 font-semibold text-gray-900">Req.</th>
                      <th className="text-center py-2 px-3 font-semibold text-gray-900">Word Limit</th>
                      <th className="text-center py-2 px-3 font-semibold text-gray-900">Required</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mockRequirements.map((req, index) => (
                      <tr key={index} className="border-b border-gray-200 hover:bg-gray-50">
                        <td className="py-3 px-3 font-medium text-gray-900">{req.section}</td>
                        <td className="text-center py-3 px-3 text-gray-600">{req.requirements}</td>
                        <td className="text-center py-3 px-3 text-gray-600">{req.wordLimit}</td>
                        <td className="text-center py-3 px-3">
                          {req.mandatory ? (
                            <span className="inline-block px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">Yes</span>
                          ) : (
                            <span className="inline-block px-2 py-1 bg-gray-100 text-gray-800 text-xs font-semibold rounded">No</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Scoring Criteria */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Scoring Criteria</h4>
              <div className="space-y-2">
                <div className="p-3 bg-gray-50 rounded border border-gray-200">
                  <p className="font-medium text-gray-900 text-sm">Project Impact & Outcomes</p>
                  <p className="text-xs text-gray-600 mt-1">40% of total score - Must demonstrate clear measurable outcomes</p>
                </div>
                <div className="p-3 bg-gray-50 rounded border border-gray-200">
                  <p className="font-medium text-gray-900 text-sm">Organizational Capacity</p>
                  <p className="text-xs text-gray-600 mt-1">25% of total score - Staffing, infrastructure, and past performance</p>
                </div>
                <div className="p-3 bg-gray-50 rounded border border-gray-200">
                  <p className="font-medium text-gray-900 text-sm">Budget & Budget Narrative</p>
                  <p className="text-xs text-gray-600 mt-1">20% of total score - Cost-effectiveness and justification</p>
                </div>
                <div className="p-3 bg-gray-50 rounded border border-gray-200">
                  <p className="font-medium text-gray-900 text-sm">Evaluation Plan</p>
                  <p className="text-xs text-gray-600 mt-1">15% of total score - Data collection and analysis methods</p>
                </div>
              </div>
            </div>

            {/* Eligibility Requirements */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Eligibility Requirements</h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex gap-2">
                  <span className="text-foam-green font-bold">✓</span>
                  <span>Must be 501(c)(3) nonprofit organization</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-foam-green font-bold">✓</span>
                  <span>Operating in Louisiana for minimum 2 years</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-foam-green font-bold">✓</span>
                  <span>Serve families and/or fatherhood initiatives</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-foam-green font-bold">✓</span>
                  <span>No organizational debt or compliance issues</span>
                </li>
              </ul>
            </div>

            {/* Formatting Requirements */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Formatting Requirements</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 bg-gray-50 rounded">
                  <p className="font-medium text-gray-900">Font</p>
                  <p className="text-gray-600">Times New Roman, 12pt</p>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <p className="font-medium text-gray-900">Spacing</p>
                  <p className="text-gray-600">Single or 1.5 line</p>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <p className="font-medium text-gray-900">Margins</p>
                  <p className="text-gray-600">1 inch on all sides</p>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <p className="font-medium text-gray-900">Format</p>
                  <p className="text-gray-600">PDF or Word Document</p>
                </div>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
