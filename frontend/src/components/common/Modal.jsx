import { X } from 'lucide-react'
import clsx from 'clsx'

export default function Modal({
  open = false,
  onClose = () => {},
  title = '',
  children,
  footer = null,
  size = 'md'
}) {
  if (!open) return null

  const sizeMap = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl'
  }

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity" onClick={onClose} />

      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className={clsx('bg-white rounded-lg shadow-xl w-full', sizeMap[size], 'max-h-[90vh] overflow-y-auto')}>
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
            <h2 className="text-xl font-bold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X size={24} className="text-gray-600" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {children}
          </div>

          {/* Footer */}
          {footer && (
            <div className="flex gap-3 p-6 border-t border-gray-200 sticky bottom-0 bg-white justify-end">
              {footer}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
