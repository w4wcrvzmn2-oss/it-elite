import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Download } from 'lucide-react'
import { useProjectStore } from '../stores/projectStore'
import { TopBar } from '../components/layout/AppLayout'
import { MetricCard, StatusBadge } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { downloadUrl } from '../api/client'
import { formatNumber } from '../lib/utils'
import { ru } from '../lib/i18n'
import { AISiteSummaryCard } from '../components/ai/AISiteSummaryCard'
import { AnalysisStatus } from '../components/analysis/AnalysisStatus'
import { ExportCenter } from '../components/export/ExportCenter'
import { generateSiteSummary } from '../api/ai'
import type { AISiteSummary } from '../types/ai'

export function ProjectOverview() {
  const navigate = useNavigate()
  const filename = useProjectStore((s) => s.filename)
  const jobStatus = useProjectStore((s) => s.jobStatus)
  const stats = useProjectStore((s) => s.statistics)
  const jobId = useProjectStore((s) => s.jobId)
  const [aiSummary, setAiSummary] = useState<AISiteSummary | null>(null)
  const [aiLoading, setAiLoading] = useState(false)

  const handleGenerateAI = async () => {
    if (!jobId) return
    setAiLoading(true)
    try {
      setAiSummary(await generateSiteSummary(jobId))
    } finally {
      setAiLoading(false)
    }
  }

  if (!stats) {
    return (
      <>
        <TopBar title="Обзор" />
        <div className="flex flex-1 flex-col items-center justify-center gap-4 text-sm text-slate-500">
          <p>Загрузите DXF, чтобы начать анализ участка.</p>
          <Link to="/"><Button size="sm">Загрузить DXF</Button></Link>
        </div>
      </>
    )
  }

  const hasTodoVerify = stats.normative_verification_required

  return (
    <>
      <TopBar title="Обзор проекта">
        {jobId && (
          <>
            <a href={downloadUrl(jobId, 'dxf')}>
              <Button variant="secondary" size="sm"><Download className="h-4 w-4" /> DXF</Button>
            </a>
            <ExportCenter jobId={jobId} />
          </>
        )}
      </TopBar>
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mb-8 rounded-2xl border border-slate-200 bg-white p-6">
          <p className="text-xs font-semibold uppercase text-green-600">{ru.productName}</p>
          <h2 className="mt-1 text-2xl font-bold text-slate-900">От DXF до готового плана озеленения</h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            Автоматически учитываем инженерные коммуникации, здания, дороги, ограничения и нормативные параметры —
            и получаем готовый план, объяснение каждого решения, ИИ-анализ и визуализацию проекта.
          </p>
          <div className="mt-4 flex gap-3">
            <Link to="/project/map"><Button size="sm">Открыть карту</Button></Link>
            <Link to="/"><Button variant="outline" size="sm">Новый проект</Button></Link>
          </div>
        </div>

        <div className="mb-2 flex items-center gap-3">
          <h3 className="text-sm font-medium text-slate-500">Инженерный анализ и автоматическое проектирование озеленения</h3>
          {jobStatus && <StatusBadge status={jobStatus.status} />}
        </div>
        <p className="mb-4 text-lg font-semibold text-slate-900">{filename}</p>

        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          <MetricCard label="Площадь участка" value={formatNumber(stats.site_area_m2)} unit="м²" onClick={() => navigate('/project/map')} />
          <MetricCard label="Разрешённая площадь" value={formatNumber(stats.allowed_area_m2)} unit="м²" onClick={() => navigate('/project/map')} />
          <MetricCard label="Ограничения" value={formatNumber(stats.forbidden_area_m2)} unit="м²" onClick={() => navigate('/project/constraints')} />
          <MetricCard label="Посадки" value={formatNumber(stats.planting_count)} onClick={() => navigate('/project/planting')} />
          <MetricCard label="Деревья" value={formatNumber(stats.tree_count)} onClick={() => navigate('/project/planting')} />
          <MetricCard label="Кустарники" value={formatNumber(stats.shrub_count)} onClick={() => navigate('/project/planting')} />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <AnalysisStatus hasTodoVerify={hasTodoVerify} />
          <AISiteSummaryCard summary={aiSummary} loading={aiLoading} onGenerate={handleGenerateAI} />
        </div>

        <div className="mt-6 rounded-2xl border border-green-200 bg-green-50 p-6">
          <p className="font-medium text-green-800">План озеленения готов</p>
          <p className="mt-1 text-sm text-green-700">
            {formatNumber(stats.planting_count)} посадок проверено на {formatNumber(stats.allowed_area_m2)} м² разрешённой зоны
          </p>
        </div>
      </div>
    </>
  )
}
