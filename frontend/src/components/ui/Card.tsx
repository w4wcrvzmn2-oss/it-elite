import { cn } from '../../lib/utils'
import { statusLabel } from '../../lib/i18n'
import type { HTMLAttributes } from 'react'

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('glass-panel rounded-2xl text-mist-50', className)}
      {...props}
    />
  )
}

export function MetricCard({
  label,
  value,
  unit,
  className,
  onClick,
}: {
  label: string
  value: string | number
  unit?: string
  className?: string
  onClick?: () => void
}) {
  return (
    <Card
      className={cn('p-4', onClick && 'cursor-pointer transition-shadow hover:shadow-md', className)}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
    >
      <p className="label-caps">{label}</p>
      <p className="mt-1 text-2xl font-extrabold tabular-nums tracking-tight text-mist-50">
        {value}
        {unit && <span className="ml-1 text-sm font-normal text-mist-400">{unit}</span>}
      </p>
    </Card>
  )
}

export function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: 'bg-green-50 text-green-700 border-green-200',
    processing: 'bg-blue-50 text-blue-700 border-blue-200',
    queued: 'bg-amber-50 text-amber-700 border-amber-200',
    error: 'bg-red-50 text-red-700 border-red-200',
    uploaded: 'bg-slate-50 text-slate-700 border-slate-200',
  }
  return (
    <span className={cn('inline-flex rounded-lg border px-2.5 py-0.5 text-xs font-medium', colors[status] || colors.uploaded)}>
      {status === 'completed' ? '✓ ' : ''}{statusLabel(status)}
    </span>
  )
}
