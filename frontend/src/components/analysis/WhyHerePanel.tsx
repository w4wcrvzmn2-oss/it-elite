import { Check, AlertTriangle } from 'lucide-react'
import type { Planting } from '../../types/api'
import { Card } from '../ui/Card'

const DIST_LABELS: Record<string, string> = {
  communication: 'До коммуникации',
  building: 'До здания',
  road: 'До дороги',
  nearest_planting: 'До соседней посадки',
}

export function WhyHerePanel({ planting }: { planting: Planting }) {
  const reasons = [
    'Точка находится внутри разрешённой зоны.',
    'Минимальные расстояния до ограничивающих объектов соблюдены.',
  ]
  Object.entries(planting.distances).forEach(([key, val]) => {
    if (val != null && DIST_LABELS[key]) {
      reasons.push(`${DIST_LABELS[key]}: ${val.toFixed(1)} м.`)
    }
  })
  reasons.push('Все проверенные геометрические ограничения соблюдены.')

  const hasTodo = planting.checks.some((c) => c.clause === 'TODO_VERIFY')

  return (
    <Card className="p-4">
      <h4 className="text-sm font-semibold text-slate-900">
        {planting.type === 'tree' ? 'Почему здесь можно посадить дерево?' : 'Почему здесь можно посадить кустарник?'}
      </h4>
      <ol className="mt-3 list-decimal space-y-2 pl-4 text-sm text-slate-600">
        {reasons.map((r, i) => (
          <li key={i}>{r}</li>
        ))}
      </ol>
      <div className="mt-4 flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2 text-xs font-medium text-green-800">
        <Check className="h-4 w-4" />
        Геометрическая проверка пройдена
      </div>
      {hasTodo && (
        <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
          <p className="flex items-start gap-1.5 font-medium">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            Нормативная проверка
          </p>
          <p className="mt-1">
            Применённое правило требует экспертной проверки перед использованием в официальном проекте.
          </p>
        </div>
      )}
    </Card>
  )
}
