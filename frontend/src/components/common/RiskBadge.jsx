import clsx from 'clsx'
import { AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react'

export default function RiskBadge({ level, label, showIcon = true }) {
  const config = {
    green: {
      bg: 'bg-emerald-100',
      text: 'text-emerald-800',
      icon: CheckCircle,
      label: label || 'Low Risk'
    },
    yellow: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-800',
      icon: AlertTriangle,
      label: label || 'Medium Risk'
    },
    red: {
      bg: 'bg-red-100',
      text: 'text-red-800',
      icon: AlertCircle,
      label: label || 'High Risk'
    }
  }

  const { bg, text, icon: Icon, label: defaultLabel } = config[level] || config.yellow

  return (
    <div className={clsx('inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium', bg, text)}>
      {showIcon && <Icon size={16} />}
      <span>{defaultLabel}</span>
    </div>
  )
}
