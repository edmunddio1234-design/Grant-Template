import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, File, Loader } from 'lucide-react'
import clsx from 'clsx'

export default function FileUpload({
  onDrop = () => {},
  files = [],
  onRemove = () => {},
  accept = '.pdf,.docx',
  multiple = false,
  disabled = false,
  loading = false,
  maxSize = 10485760
}) {
  const onDropCallback = useCallback((acceptedFiles) => {
    onDrop(acceptedFiles)
  }, [onDrop])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onDropCallback,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    multiple,
    disabled: disabled || loading,
    maxSize
  })

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer',
          isDragActive
            ? 'border-foam-primary bg-blue-50'
            : 'border-gray-300 bg-white hover:border-gray-400',
          (disabled || loading) && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-3">
          {loading ? (
            <Loader size={32} className="text-foam-primary animate-spin" />
          ) : (
            <Upload size={32} className="text-gray-400" />
          )}

          <div>
            <p className="font-semibold text-gray-900">
              {isDragActive ? 'Drop files here' : 'Drag and drop files here'}
            </p>
            <p className="text-sm text-gray-500">
              or click to select from your computer
            </p>
            <p className="text-xs text-gray-400 mt-2">
              Supported formats: PDF, DOCX | Max size: 10MB
            </p>
          </div>
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-semibold text-gray-900 text-sm">Selected Files</h4>
          <div className="space-y-2">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg"
              >
                <File size={18} className="text-gray-400" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                </div>
                <button
                  onClick={() => onRemove(index)}
                  className="p-1 hover:bg-gray-200 rounded transition-colors"
                >
                  <X size={18} className="text-gray-600" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
