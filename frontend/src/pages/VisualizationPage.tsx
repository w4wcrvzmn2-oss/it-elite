import { useCallback, useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { generateVisualizations, getVisualizations, visualizationImageUrl, type VisualizationItem } from '../api/visualizations'
import { TopBar } from '../components/layout/AppLayout'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useProjectStore } from '../stores/projectStore'

export function VisualizationPage() {
  const jobId = useProjectStore((s) => s.jobId)
  const [items, setItems] = useState<VisualizationItem[]>([])
  const [status, setStatus] = useState('not_started')
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    if (!jobId) return
    const data = await getVisualizations(jobId)
    setItems(data.visualizations || [])
    setStatus(data.status)
  }, [jobId])

  useEffect(() => {
    load()
    const t = setInterval(() => {
      if (status === 'processing') load()
    }, 2000)
    return () => clearInterval(t)
  }, [load, status])

  const handleGenerate = async () => {
    if (!jobId) return
    setLoading(true)
    setStatus('processing')
    await generateVisualizations(jobId)
    setLoading(false)
  }

  const aiItems = items.filter((v) => v.ai_generated || v.kind === 'ai')
  const planItems = items.filter((v) => !v.ai_generated && v.kind !== 'ai')
  const displayItems = aiItems.length > 0 ? aiItems : planItems

  if (!jobId) {
    return (
      <>
        <TopBar title="Визуализация" />
        <div className="flex flex-1 items-center justify-center text-sm text-slate-500">
          Загрузите DXF и выполните расчёт
        </div>
      </>
    )
  }

  return (
    <>
      <TopBar title="Визуализация">
        <Button size="sm" onClick={handleGenerate} disabled={loading || status === 'processing'}>
          {loading || status === 'processing' ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          Создать визуализации
        </Button>
      </TopBar>
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mb-6 max-w-2xl">
          <h2 className="text-lg font-semibold text-slate-900">Как будет выглядеть территория после озеленения</h2>
          <p className="mt-1 text-sm text-slate-500">
            Сначала формируется инженерный план (matplotlib), затем — AI-визуализация при наличии OPENROUTER_IMAGE_MODEL.
          </p>
          <p className="mt-2 text-xs text-amber-700">
            Генерация изображений может расходовать API-баланс. AI-визуализация не заменяет инженерный чертёж.
          </p>
        </div>

        {status === 'processing' && (
          <div className="mb-6 space-y-1 text-sm text-slate-500">
            <p>Подготовка плана…</p>
            <p>Анализ состава посадок…</p>
            <p>Формирование описания…</p>
            <p>Генерация AI-изображений…</p>
          </div>
        )}

        {planItems.length > 0 && aiItems.length > 0 && (
          <p className="mb-4 text-sm text-slate-600">
            Показаны AI-визуализации. Инженерные планы доступны в ZIP (06_visualizations/plan_*.png).
          </p>
        )}

        <div className="grid gap-6 md:grid-cols-3">
          {displayItems.map((v) => (
            <Card key={v.id} className="overflow-hidden">
              <img
                src={visualizationImageUrl(jobId, v.id)}
                alt={v.title}
                className="aspect-video w-full object-cover"
              />
              <div className="p-4">
                <p className="text-sm font-medium text-slate-900">{v.title}</p>
                <p className="mt-1 text-[10px] text-slate-400">{v.badge}</p>
                {v.ai_generated && (
                  <p className="mt-1 text-[10px] font-medium text-green-700">AI-визуализация</p>
                )}
              </div>
            </Card>
          ))}
        </div>

        {displayItems.length === 0 && status !== 'processing' && (
          <p className="text-sm text-slate-500">Нажмите «Создать визуализации» для генерации.</p>
        )}
      </div>
    </>
  )
}
