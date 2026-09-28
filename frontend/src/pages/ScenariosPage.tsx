import { useCallback, useEffect, useState } from 'react'
import { Loader2, Sparkles } from 'lucide-react'
import { compareScenariosAI } from '../api/ai'
import { generateScenarios, getScenarios, type ScenarioItem } from '../api/scenarios'
import { TopBar } from '../components/layout/AppLayout'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useProjectStore } from '../stores/projectStore'
import { formatNumber } from '../lib/utils'
import type { ScenarioComparisonAI } from '../types/ai'

export function ScenariosPage() {
  const jobId = useProjectStore((s) => s.jobId)
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([])
  const [status, setStatus] = useState('not_started')
  const [loading, setLoading] = useState(false)
  const [aiCompare, setAiCompare] = useState<ScenarioComparisonAI | null>(null)
  const [comparison, setComparison] = useState<{ rows: { metric: string; values: Record<string, number> }[] }>({ rows: [] })

  const load = useCallback(async () => {
    if (!jobId) return
    const data = await getScenarios(jobId)
    setScenarios(data.scenarios || [])
    setStatus(data.status)
    setComparison(data.comparison || { rows: [] })
  }, [jobId])

  useEffect(() => {
    load()
    const t = setInterval(() => {
      if (status === 'processing') load()
    }, 3000)
    return () => clearInterval(t)
  }, [load, status])

  const handleGenerate = async () => {
    if (!jobId) return
    setLoading(true)
    setStatus('processing')
    await generateScenarios(jobId)
    setLoading(false)
  }

  const handleAiCompare = async () => {
    if (!jobId) return
    setLoading(true)
    try {
      setAiCompare(await compareScenariosAI(jobId))
    } finally {
      setLoading(false)
    }
  }

  if (!jobId) {
    return (
      <>
        <TopBar title="Сценарии" />
        <div className="flex flex-1 items-center justify-center text-sm text-slate-500">
          Загрузите DXF и выполните расчёт
        </div>
      </>
    )
  }

  return (
    <>
      <TopBar title="Сценарии">
        <Button size="sm" onClick={handleGenerate} disabled={loading || status === 'processing'}>
          {status === 'processing' ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          Создать сценарии
        </Button>
      </TopBar>
      <div className="flex-1 overflow-y-auto p-6">
        {status === 'processing' && (
          <p className="mb-4 text-sm text-slate-500">Расчёт сценариев… каждый вариант рассчитывается детерминированным ядром.</p>
        )}

        <div className="grid gap-4 md:grid-cols-3">
          {scenarios.map((s) => (
            <Card key={s.id} className="p-5">
              <h3 className="font-semibold text-slate-900">{s.name}</h3>
              <p className="mt-1 text-xs text-slate-500">{s.description}</p>
              <dl className="mt-4 space-y-1 text-sm">
                <div className="flex justify-between"><dt className="text-slate-500">Деревья</dt><dd className="font-medium tabular-nums">{formatNumber(s.tree_count)}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Кустарники</dt><dd className="font-medium tabular-nums">{formatNumber(s.shrub_count)}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Всего</dt><dd className="font-medium tabular-nums">{formatNumber(s.planting_count)}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Плотность</dt><dd className="font-medium tabular-nums">{s.density_per_1000m2.toFixed(1)} / 1000 м²</dd></div>
              </dl>
            </Card>
          ))}
        </div>

        {comparison.rows.length > 0 && (
          <Card className="mt-6 overflow-x-auto p-5">
            <h3 className="text-sm font-semibold text-slate-900">Сравнение вариантов</h3>
            <table className="mt-4 w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                  <th className="pb-2 pr-4">Показатель</th>
                  {scenarios.map((s) => (
                    <th key={s.id} className="pb-2 pr-4">{s.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparison.rows.map((row) => (
                  <tr key={row.metric} className="border-b border-slate-100">
                    <td className="py-2 pr-4 text-slate-600">{row.metric}</td>
                    {scenarios.map((s) => (
                      <td key={s.id} className="py-2 pr-4 tabular-nums">
                        {typeof row.values[s.id] === 'number'
                          ? row.values[s.id] % 1 === 0
                            ? formatNumber(row.values[s.id])
                            : row.values[s.id].toFixed(1)
                          : '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <Button className="mt-4" variant="outline" size="sm" onClick={handleAiCompare} disabled={loading}>
              <Sparkles className="h-4 w-4" />
              Сравнить с помощью ИИ
            </Button>
          </Card>
        )}

        {aiCompare && (
          <Card className="mt-4 p-5">
            <h3 className="text-sm font-semibold text-slate-900">ИИ-анализ различий</h3>
            {aiCompare.fallback && <p className="mt-1 text-xs text-amber-600">ИИ временно недоступен</p>}
            <p className="mt-2 text-sm text-slate-600">{aiCompare.summary}</p>
            <ul className="mt-3 space-y-1 text-sm text-slate-600">
              {aiCompare.differences.map((d, i) => (
                <li key={i}>• {d}</li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </>
  )
}
