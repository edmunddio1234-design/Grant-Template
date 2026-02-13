import clsx from 'clsx'

const tagColors = {
  program: 'bg-blue-100 text-blue-800',
  funding: 'bg-green-100 text-green-800',
  evidence: 'bg-purple-100 text-purple-800',
  priority: 'bg-amber-100 text-amber-800',
  requirement: 'bg-red-100 text-red-800',
  default: 'bg-gray-100 text-gray-800'
}

export default function TagList({ tags = [], variant = 'default', onRemove = null, editable = false }) {
  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag, index) => {
        const type = typeof tag === 'string' ? tag : tag.type || 'default'
        const label = typeof tag === 'string' ? tag : tag.label || tag.name
        const color = tagColors[type] || tagColors.default

        return (
          <span
            key={index}
            className={clsx(
              'inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium transition-colors',
              color,
              editable && onRemove && 'cursor-pointer hover:opacity-80'
            )}
            onClick={() => editable && onRemove && onRemove(index)}
          >
            {label}
            {editable && onRemove && <span className="ml-1">×</span>}
          </span>
        )
      })}
      {tags.length === 0 && <span className="text-sm text-gray-500">No tags</span>}
    </div>
  )
}
