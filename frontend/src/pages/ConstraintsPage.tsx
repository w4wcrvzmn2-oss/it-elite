import { AlertTriangle, Check } from 'lucide-react'
import { useProjectStore } from '../stores/projectStore'
import { TopBar } from '../components/layout/AppLayout'
import { Card } from '../components/ui/Card'
import { NormativeStatusCard } from '../components/normative/NormativeStatusCard'
import type { NormativeRule } from '../components/normative/NormativeStatusCard'

function ruleLabel(rule: string): string {
  const map: Record<string, string> = {
    communication_distance: 'Коммуникации',
    building_distance: 'Здания',
    road_distance: 'Дороги',
    minimum_spacing: 'Межрастительное расстояние',
  }
  return map[rule] || rule.replace('_', ' ')
}

export function ConstraintsPage() {
  const stats = useProjectStore((s) => s.statistics)
  const plantings = useProjectStore((s) => s.plantings)

  const rulesFromStats = (stats?.rules_applied ?? []) as NormativeRule[]
  const sampleChecks = plantings[0]?.checks ?? []
  const displayRules: NormativeRule[] = rulesFromStats.length > 0
    ? rulesFromStats
    : sampleChecks.map((c) => ({
        rule: c.rule,
        regulation: c.regulation,
        clause: c.clause,
        description: c.description,
        minimum_distance: c.required,
      }))

  return (
    <>
      <TopBar title="Ограничения" />
      <div className="flex-1 overflow-y-auto p-6">
        <p className="mb-6 text-sm text-slate-500">
          Правила, применённые при оптимизации посадок. Все пункты с TODO_VERIFY требуют экспертной проверки.
        </p>

        {displayRules.length > 0 && (
          <div className="mb-6">
            <NormativeStatusCard rules={displayRules} />
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          {sampleChecks.filter((c) => c.status === 'passed' || c.required > 0).map((check) => (
            <Card key={check.rule + check.regulation} className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {ruleLabel(check.rule)}
                  </p>
                  <p className="mt-2 text-sm text-slate-600">
                    {check.rule === 'minimum_spacing' ? 'Мин. расстояние' : 'Мин. отступ'}:
                  </p>
                  <p className="text-2xl font-semibold tabular-nums text-slate-900">
                    {check.required.toFixed(1)} м
                  </p>
                  <p className="mt-2 text-sm text-slate-500">Источник: {check.regulation}</p>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className="inline-flex items-center gap-1 rounded-lg bg-green-50 px-2 py-1 text-xs text-green-700">
                    <Check className="h-3 w-3" /> Активно
                  </span>
                  {check.clause === 'TODO_VERIFY' && (
                    <span className="inline-flex items-center gap-1 rounded-lg bg-amber-50 px-2 py-1 text-xs text-amber-700">
                      <AlertTriangle className="h-3 w-3" /> Требует проверки
                    </span>
                  )}
                </div>
              </div>
            </Card>
          ))}

          {stats?.planting_config && Object.entries(stats.planting_config).map(([type, cfg]) => (
            <Card key={type} className="p-5">
              <p className="text-xs font-semibold uppercase text-slate-500">
                {type === 'tree' ? 'Деревья' : 'Кустарники'} — шаг сетки
              </p>
              <p className="mt-2 text-2xl font-semibold tabular-nums">{cfg.min_spacing} м</p>
              <p className="mt-1 text-sm text-slate-500">Источник: СП 42.13330.2016</p>
              <span className="mt-2 inline-flex items-center gap-1 rounded-lg bg-amber-50 px-2 py-1 text-xs text-amber-700">
                <AlertTriangle className="h-3 w-3" /> TODO_VERIFY
              </span>
            </Card>
          ))}
        </div>
      </div>
    </>
  )
}
