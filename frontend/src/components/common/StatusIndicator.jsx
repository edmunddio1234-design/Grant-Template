import clsx from 'clsx'
import {
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle,
  Loader,
  FileText
} from 'lucide-react'

const statusConfig = {
  active: {
    icon: CheckCircle,
    color: 'text-emerald-600',
    bg: 'bg-emerald-50',
    label: 'Active'
  },
  pending: {
    icon: Clock,
    color: 'text-amber-600',
    bg: 'bg-amber-50',
    label: 'Pending'
  },
  warning: {
    icon: AlertCircle,
    color: 'text-orange-600',
    bg: 'bg-orange-50',
    label: 'Warning'
  },
  error: {
    icon: XCircle,
    color: 'text-red-600',
    bg: 'bg-red-50',
    label: 'Error'
  },
  loading: {
    icon: Loader,
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    label: 'Loading',
    animate: true
  },
  draft: {
    icon: FileText,
    color: 'text-gray-600',
    bg: 'bg-gray-50',
    label: 'Draft'
  },
  published: {
    icon: CheckCircle,
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    label: 'Published'
  }
}

export default function StatusIndicator({ status = 'pending', label = null, size = 'md', showBg = true }) {
  const config = statusConfig[status] || statusConfig.pending
  const Icon = config.icon

  const sizeMap = {
    sm: { icon: 16, text: 'text-xs' },
    md: { icon: 20, text: 'text-sm' },
    lg: { icon: 24, text: 'text-base' }
  }

  const { icon: iconSize, text: textSize } = sizeMap[size]

  return (
    <div className={clsx(
      'inline-flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
      showBg ? config.bg : 'bg-transparent'
    )}>
      <Icon
        size={iconSize}
        className={clsx(config.color, config.animate && 'animate-spin')}
      />
      <span className={clsx('font-medium', config.color, textSize)}>
        {label || config.label}
      </span>
    </div>
  )
}
