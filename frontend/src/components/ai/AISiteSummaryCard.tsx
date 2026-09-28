import { Sparkles } from 'lucide-react'
import type { AISiteSummary } from '../../types/ai'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { ru } from '../../lib/i18n'

export function AISiteSummaryCard({
  summary,
  loading,
  onGenerate,
}: {
  summary: AISiteSummary | null
  loading: boolean
  onGenerate: () => void
}) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-green-600" />
          <h3 className="text-sm font-semibold text-slate-900">GREEN PLANNER AI</h3>
        </div>
        {!summary && (
          <Button size="sm" onClick={onGenerate} disabled={loading}>
            {loading ? 'Анализ…' : 'Сделать краткий анализ участка'}
          </Button>
        )}
      </div>
      <p className="mt-1 text-[10px] text-slate-400">{ru.aiSubtitle}</p>

      {summary && (
        <div className="mt-4 space-y-3">
          {summary.fallback && (
            <p className="text-xs text-amber-600">ИИ временно недоступен — показан детерминированный анализ</p>
          )}
          <p className="text-sm leading-relaxed text-slate-700">{summary.summary}</p>
          <ul className="space-y-1 text-sm text-slate-600">
            {summary.key_metrics.map((m, i) => (
              <li key={i}>• {m}</li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  )
}
