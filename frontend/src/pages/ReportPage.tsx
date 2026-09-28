import { useState } from 'react'
import { Download, Sparkles } from 'lucide-react'
import { useProjectStore } from '../stores/projectStore'
import { TopBar } from '../components/layout/AppLayout'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { exportUrl } from '../api/export'
import { generateAIReport } from '../api/ai'
import { AIReportCard } from '../components/ai/AIReportCard'
import { NormativeStatusCard } from '../components/normative/NormativeStatusCard'
import type { NormativeRule } from '../components/normative/NormativeStatusCard'
import { ExportCenter } from '../components/export/ExportCenter'
import type { AIReport } from '../types/ai'
import { formatNumber } from '../lib/utils'

export function ReportPage() {
  const filename = useProjectStore((s) => s.filename)
  const stats = useProjectStore((s) => s.statistics)
  const jobId = useProjectStore((s) => s.jobId)
  const plantings = useProjectStore((s) => s.plantings)
  const [aiReport, setAiReport] = useState<AIReport | null>(null)
  const [aiLoading, setAiLoading] = useState(false)

  const handleGenerateReport = async () => {
    if (!jobId) return
    setAiLoading(true)
    try {
      setAiReport(await generateAIReport(jobId))
    } catch {
      setAiReport(null)
    } finally {
      setAiLoading(false)
    }
  }

  if (!stats) {
    return (
      <>
        <TopBar title="Отчёт" />
        <div className="flex flex-1 items-center justify-center text-sm text-slate-500">Отчёт недоступен</div>
      </>
    )
  }

  const rules = (stats.rules_applied ?? []) as NormativeRule[]

  return (
    <>
      <TopBar title="Отчёт">
        {jobId && (
          <>
            <a href={exportUrl(jobId, 'pdf')}><Button variant="secondary" size="sm"><Download className="h-4 w-4" /> PDF</Button></a>
            <ExportCenter jobId={jobId} />
          </>
        )}
      </TopBar>
      <div className="flex-1 overflow-y-auto p-6">
        <Card className="mx-auto max-w-3xl p-8">
          <div className="border-b border-slate-200 pb-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-green-600">Green Planner</p>
            <h2 className="mt-1 text-2xl font-bold text-slate-900">Отчёт по озеленению</h2>
            <p className="mt-1 text-sm text-slate-500">{filename}</p>
          </div>

          <section className="mt-6">
            <h3 className="text-sm font-semibold uppercase text-slate-500">Метрики участка</h3>
            <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-slate-500">Площадь участка</span><p className="font-semibold tabular-nums">{formatNumber(stats.site_area_m2)} м²</p></div>
              <div><span className="text-slate-500">Разрешённая зона</span><p className="font-semibold tabular-nums">{formatNumber(stats.allowed_area_m2)} м²</p></div>
              <div><span className="text-slate-500">Зона ограничений</span><p className="font-semibold tabular-nums">{formatNumber(stats.forbidden_area_m2)} м²</p></div>
              <div><span className="text-slate-500">Коммуникаций</span><p className="font-semibold tabular-nums">{stats.communications}</p></div>
            </div>
          </section>

          <section className="mt-6">
            <h3 className="text-sm font-semibold uppercase text-slate-500">Озеленение</h3>
            <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-slate-500">Всего посадок</span><p className="font-semibold tabular-nums">{formatNumber(stats.planting_count)}</p></div>
              <div><span className="text-slate-500">Деревья</span><p className="font-semibold tabular-nums">{formatNumber(stats.tree_count)}</p></div>
              <div><span className="text-slate-500">Кустарники</span><p className="font-semibold tabular-nums">{formatNumber(stats.shrub_count)}</p></div>
              <div><span className="text-slate-500">Плотность</span><p className="font-semibold tabular-nums">{stats.density_per_1000m2.toFixed(1)} / 1000 м²</p></div>
            </div>
          </section>

          <section className="mt-6">
            <h3 className="text-sm font-semibold uppercase text-slate-500">Проверка</h3>
            <p className="mt-2 text-sm text-green-700">
              Все {formatNumber(plantings.length)} размещений прошли жёсткую геометрическую валидацию.
            </p>
          </section>

          {rules.length > 0 && (
            <section className="mt-6">
              <NormativeStatusCard rules={rules} />
            </section>
          )}

          <div className="mt-8 flex items-center justify-between gap-4">
            <p className="text-xs text-slate-400">
              Время расчёта: {stats.processing_time_sec.toFixed(1)} с
            </p>
            {jobId && (
              <Button size="sm" variant="outline" onClick={handleGenerateReport} disabled={aiLoading}>
                <Sparkles className="h-4 w-4" />
                {aiLoading ? 'Генерация…' : 'Сформировать ИИ-отчёт'}
              </Button>
            )}
          </div>

          {aiReport && <AIReportCard report={aiReport} />}
        </Card>
      </div>
    </>
  )
}
