import { Check, Circle, Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

const STEPS = [
  { key: 'import', label: 'Импорт', desc: 'Чтение CAD-сущностей' },
  { key: 'geometry', label: 'Анализ', desc: 'Анализ геометрии участка' },
  { key: 'restrictions', label: 'Ограничения', desc: 'Построение буферов ограничений' },
  { key: 'optimization', label: 'Посадки', desc: 'Поиск кандидатов на посадку' },
  { key: 'validation', label: 'Проверка', desc: 'Валидация каждой точки' },
  { key: 'export', label: 'Экспорт', desc: 'Формирование результата DXF' },
]

function stepIndex(progress: number): number {
  if (progress >= 100) return 6
  if (progress >= 95) return 5
  if (progress >= 80) return 4
  if (progress >= 60) return 3
  if (progress >= 40) return 2
  if (progress >= 25) return 1
  if (progress >= 10) return 0
  return 0
}

export function ProcessingStepper({ progress, stage }: { progress: number; stage: string }) {
  const active = stepIndex(progress)

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div className="text-center">
        <Loader2 className="mx-auto h-8 w-8 animate-spin text-leaf" />
        <p className="label-caps mt-3">Генерация</p>
        <p className="mt-1 text-lg font-extrabold tracking-tight text-mist-50">{stage}</p>
        <p className="mt-1 text-sm text-mist-500 tabular-nums">{progress}%</p>
      </div>
      <div className="space-y-3">
        {STEPS.map((step, i) => {
          const done = i < active
          const current = i === active
          return (
            <div key={step.key} className="flex items-center gap-3">
              <div className={cn(
                'flex h-8 w-8 items-center justify-center rounded-full border',
                done && 'border-leaf bg-leaf text-leaf-ink',
                current && 'border-leaf bg-leaf/20 text-leaf',
                !done && !current && 'border-white/10 text-mist-500',
              )}>
                {done ? <Check className="h-4 w-4" /> : current ? <Loader2 className="h-4 w-4 animate-spin" /> : <Circle className="h-3 w-3" />}
              </div>
              <div>
                <p className={cn('text-sm font-semibold', current || done ? 'text-mist-50' : 'text-mist-400')}>
                  {String(i + 1).padStart(2, '0')} {step.label}
                </p>
                {current && <p className="text-[11px] text-mist-500">{step.desc}</p>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
