import { useEffect, useState } from 'react'
import { AlertCircle, CheckCircle2, Sparkles } from 'lucide-react'
import { getAIStatus } from '../../api/ai'
import type { AIStatus as AIStatusType } from '../../types/ai'
import { Card } from '../ui/Card'
import { ru } from '../../lib/i18n'

export function AIStatus() {
  const [status, setStatus] = useState<AIStatusType | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAIStatus()
      .then(setStatus)
      .catch(() => setStatus(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <Card className="p-6">
        <p className="text-sm text-slate-500">Проверка статуса ИИ…</p>
      </Card>
    )
  }

  if (!status) {
    return (
      <Card className="p-6">
        <p className="text-sm text-slate-500">Статус ИИ недоступен</p>
      </Card>
    )
  }

  const available = status.enabled && status.available

  return (
    <Card className="p-6">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-green-600" />
        <h3 className="text-sm font-semibold text-slate-900">GREEN PLANNER AI</h3>
      </div>
      <p className="mt-1 text-xs text-slate-500">{ru.aiSubtitle}</p>

      <div className="mt-4 flex items-start gap-3">
        {available ? (
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-green-600" />
        ) : (
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" />
        )}
        <div>
          <p className="text-sm font-medium text-slate-900">
            {available ? '● Подключён' : '○ ИИ недоступен'}
          </p>
          <p className="mt-1 text-sm text-slate-600">{status.message}</p>
          {status.model && <p className="mt-2 text-xs text-slate-500">Модель: {status.model}</p>}
          {status.last_latency_sec != null && (
            <p className="text-xs text-slate-500">Последний ответ: {status.last_latency_sec} с</p>
          )}
          {status.last_tokens != null && (
            <p className="text-xs text-slate-500">Токены: {status.last_tokens}</p>
          )}
          <p className="mt-2 text-xs text-slate-400">Ключ API: ••••••••</p>
        </div>
      </div>

      {!available && (
        <p className="mt-4 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
          Основной алгоритм продолжает работать без ИИ. Задайте OPENROUTER_API_KEY в backend .env.
        </p>
      )}
    </Card>
  )
}
