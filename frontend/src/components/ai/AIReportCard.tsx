import { AlertTriangle, Sparkles } from 'lucide-react'
import type { AIReport } from '../../types/ai'
import { Card } from '../ui/Card'

export function AIReportCard({ report }: { report: AIReport }) {
  return (
    <div className="mt-6 space-y-4 border-t border-slate-200 pt-6">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-green-600" />
        <h3 className="text-sm font-semibold uppercase text-slate-500">ИИ-отчёт</h3>
      </div>
      <p className="text-[10px] text-slate-400">На основе детерминированного расчёта</p>

      {report.fallback && (
        <div className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
          ИИ временно недоступен — показано детерминированное резюме
        </div>
      )}

      <Card className="p-4">
        <h4 className="text-lg font-semibold text-slate-900">{report.title}</h4>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">{report.overview}</p>
      </Card>

      {report.sections.map((section) => (
        <section key={section.title}>
          <h4 className="text-sm font-semibold text-slate-900">{section.title}</h4>
          <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-slate-600">{section.content}</p>
        </section>
      ))}

      {report.verification_notes.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
          {report.verification_notes.map((note) => (
            <p key={note} className="flex items-start gap-1.5 text-xs text-amber-800">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              {note}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
