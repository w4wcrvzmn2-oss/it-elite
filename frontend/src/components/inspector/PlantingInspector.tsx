import { useEffect, useState } from 'react'
import { AlertTriangle, Check, Sparkles } from 'lucide-react'
import type { Planting } from '../../types/api'
import type { AIExplanation } from '../../types/ai'
import { explainPlanting } from '../../api/ai'
import { useProjectStore } from '../../stores/projectStore'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { AIExplanationCard } from '../ai/AIExplanationCard'
import { AIAssistant } from '../ai/AIAssistant'
import { WhyHerePanel } from '../analysis/WhyHerePanel'
import { ru } from '../../lib/i18n'

function ruleLabel(rule: string): string {
  const map: Record<string, string> = {
    communication_distance: 'Коммуникации',
    building_distance: 'Здания',
    road_distance: 'Дороги',
    minimum_spacing: 'Межрастительное расстояние',
  }
  return map[rule] || rule
}

function RuleCard({ check }: { check: Planting['checks'][0] }) {
  const passed = check.status === 'passed'
  return (
    <Card className="p-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {ruleLabel(check.rule)}
          </p>
          {check.value != null && (
            <p className="mt-1 text-lg font-semibold tabular-nums text-slate-900">
              {check.value.toFixed(1)} м
            </p>
          )}
          <p className="text-xs text-slate-500">Требуется ≥ {check.required.toFixed(1)} м</p>
        </div>
        <div className={passed ? 'text-green-600' : 'text-red-500'}>
          {passed ? <Check className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
        </div>
      </div>
    </Card>
  )
}

export function PlantingInspector({
  planting,
  whyNot,
}: {
  planting: Planting | null
  whyNot?: { title: string; reasons: string[] } | null
}) {
  const jobId = useProjectStore((s) => s.jobId)
  const [showWhyHere, setShowWhyHere] = useState(false)
  const [aiExplanation, setAiExplanation] = useState<AIExplanation | null>(null)
  const [aiLoading, setAiLoading] = useState(false)

  useEffect(() => {
    setAiExplanation(null)
    setShowWhyHere(false)
  }, [planting?.id, whyNot])

  const handleExplain = async () => {
    if (!jobId || !planting) return
    setAiLoading(true)
    try {
      setAiExplanation(await explainPlanting(jobId, planting.id))
    } catch {
      setAiExplanation(null)
    } finally {
      setAiLoading(false)
    }
  }

  if (whyNot) {
    return (
      <div className="flex h-full flex-col overflow-y-auto p-4">
        <h3 className="text-lg font-semibold text-slate-900">{whyNot.title}</h3>
        <ul className="mt-4 space-y-2 text-sm text-slate-600">
          {whyNot.reasons.map((r, i) => (
            <li key={i} className="flex gap-2"><span className="text-red-500">•</span>{r}</li>
          ))}
        </ul>
        <AIAssistant />
      </div>
    )
  }

  if (!planting) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex flex-1 flex-col items-center justify-center p-6 text-center">
          <p className="text-sm text-slate-500">Выберите посадку на карте или кликните по пустой зоне</p>
        </div>
        <AIAssistant />
      </div>
    )
  }

  const passedChecks = planting.checks.filter((c) => c.status === 'passed')
  const num = planting.id.replace(/\D/g, '') || planting.id

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="border-b border-slate-200 p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {planting.type === 'tree' ? 'Дерево' : 'Кустарник'}
        </p>
        <h3 className="text-lg font-semibold text-slate-900">Посадка №{num}</h3>
        <div className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700">
          <Check className="h-3.5 w-3.5" />
          Допустимо
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div><span className="text-slate-500">X</span><p className="font-mono tabular-nums">{planting.x.toFixed(2)}</p></div>
          <div><span className="text-slate-500">Y</span><p className="font-mono tabular-nums">{planting.y.toFixed(2)}</p></div>
        </div>
        <Button size="sm" className="mt-3 w-full" onClick={() => setShowWhyHere(true)}>
          Почему здесь?
        </Button>
        <Button size="sm" variant="outline" className="mt-2 w-full" onClick={handleExplain} disabled={aiLoading}>
          <Sparkles className="h-3.5 w-3.5" />
          {aiLoading ? 'Генерация…' : 'Объяснить с помощью ИИ'}
        </Button>
      </div>

      {showWhyHere && (
        <div className="border-b border-slate-200 p-4">
          <WhyHerePanel planting={planting} />
        </div>
      )}

      <div className="space-y-3 p-4">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Расстояния</h4>
        {passedChecks.map((check) => (
          <RuleCard key={check.rule} check={check} />
        ))}
      </div>

      <div className="border-t border-slate-200 p-4">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Нормативная база</h4>
        <div className="mt-2 space-y-2">
          {passedChecks.filter((c) => c.regulation && c.regulation !== 'CONFIG').map((check) => (
            <div key={`${check.regulation}-${check.rule}`} className="rounded-xl border border-slate-200 p-3">
              <p className="text-sm font-medium text-slate-900">{check.regulation}</p>
              <p className="text-xs text-slate-500">Пункт: {check.clause}</p>
              {check.clause === 'TODO_VERIFY' && (
                <div className="mt-2 flex items-center gap-1.5 text-xs text-amber-700">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Пункт требует экспертной проверки
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {aiExplanation && <AIExplanationCard explanation={aiExplanation} />}

      <div className="border-t border-slate-200 p-4">
        <p className="text-[10px] text-slate-400">{ru.aiSubtitle}</p>
        <AIAssistant />
      </div>
    </div>
  )
}
