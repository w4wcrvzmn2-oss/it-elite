import { AlertTriangle, CheckCircle2, FileWarning } from 'lucide-react'
import { Card } from '../ui/Card'

export interface NormativeRule {
  rule?: string
  regulation?: string
  document?: string
  clause?: string
  description?: string
  minimum_distance?: number
}

export function NormativeStatusCard({ rules }: { rules: NormativeRule[] }) {
  const todoRules = rules.filter((r) => r.clause === 'TODO_VERIFY')
  const verifiedCount = rules.length - todoRules.length

  return (
    <Card className="p-5">
      <div className="flex items-start gap-3">
        {todoRules.length > 0 ? (
          <FileWarning className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
        ) : (
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-green-600" />
        )}
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-slate-900">Нормативная проверка</h3>
          <p className="mt-1 text-sm text-slate-600">
            Применено правил: {rules.length}. Подтверждено пунктов: {verifiedCount}.
          </p>
          {todoRules.length > 0 && (
            <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
              ⚠ {todoRules.length} правил имеют статус TODO_VERIFY — требуется экспертная верификация.
              Система не подставляет номера пунктов нормативных документов.
            </p>
          )}
        </div>
      </div>

      <ul className="mt-4 space-y-2">
        {rules.map((r, i) => {
          const doc = r.regulation || r.document || '—'
          const isTodo = r.clause === 'TODO_VERIFY'
          return (
            <li key={`${doc}-${r.rule}-${i}`} className="flex items-start gap-2 rounded-lg border border-slate-100 p-3 text-sm">
              {isTodo ? (
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
              ) : (
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-green-600" />
              )}
              <div>
                <p className="font-medium text-slate-900">{doc}</p>
                <p className="text-xs text-slate-500">{r.description || r.rule}</p>
                {r.minimum_distance != null && (
                  <p className="text-xs text-slate-600">Мин. расстояние: {r.minimum_distance} м</p>
                )}
                <p className={`mt-1 text-xs ${isTodo ? 'text-amber-700' : 'text-green-700'}`}>
                  Пункт: {r.clause || 'TODO_VERIFY'}
                  {isTodo && ' — требует экспертной проверки'}
                </p>
              </div>
            </li>
          )
        })}
      </ul>
    </Card>
  )
}
