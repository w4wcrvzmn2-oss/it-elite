import { Check, AlertTriangle } from 'lucide-react'
import { Card } from '../ui/Card'

const STEPS = [
  'DXF успешно загружен',
  'Геометрия распознана',
  'Коммуникации определены',
  'Зоны ограничений построены',
  'Разрешённая зона рассчитана',
  'Кандидаты сгенерированы',
  'Посадки проверены',
  'Результат экспортирован',
]

export function AnalysisStatus({ hasTodoVerify }: { hasTodoVerify: boolean }) {
  return (
    <Card className="p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Статус анализа</h3>
      <ul className="mt-4 space-y-2">
        {STEPS.map((step) => (
          <li key={step} className="flex items-center gap-2 text-sm text-slate-700">
            <Check className="h-4 w-4 shrink-0 text-green-600" />
            {step}
          </li>
        ))}
        {hasTodoVerify && (
          <li className="flex items-start gap-2 text-sm text-amber-800">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            Нормативные пункты требуют экспертной верификации
          </li>
        )}
      </ul>
    </Card>
  )
}
