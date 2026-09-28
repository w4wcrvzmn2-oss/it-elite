import { AlertTriangle, Sparkles } from 'lucide-react'
import type { AIExplanation } from '../../types/ai'
import { Card } from '../ui/Card'

export function AIExplanationCard({ explanation }: { explanation: AIExplanation }) {
  return (
    <div className="space-y-3 border-t border-slate-200 p-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-green-600" />
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">ИИ-объяснение</h4>
      </div>
      <p className="text-[10px] text-slate-400">На основе детерминированного расчёта</p>

      {explanation.fallback && (
        <div className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
          ИИ временно недоступен — показано детерминированное объяснение
        </div>
      )}

      <Card className="p-3">
        <p className="text-sm font-medium text-slate-900">{explanation.title}</p>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">{explanation.summary}</p>
      </Card>

      {explanation.reasons.length > 0 && (
        <ul className="space-y-1 text-sm text-slate-600">
          {explanation.reasons.map((r, i) => (
            <li key={i} className="flex gap-2"><span className="text-green-600">✓</span>{r}</li>
          ))}
        </ul>
      )}

      {explanation.verification_notes.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
          {explanation.verification_notes.map((n, i) => (
            <p key={i} className="flex items-start gap-1.5 text-xs text-amber-800">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              {n}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
