import { useState } from 'react'
import { Loader2, Send, Sparkles } from 'lucide-react'
import { askAI } from '../../api/ai'
import { useProjectStore } from '../../stores/projectStore'
import { Button } from '../ui/Button'

const QUICK_QUESTIONS = [
  'Почему здесь можно посадить дерево?',
  'Почему здесь нет посадок?',
  'Какие ограничения сильнее всего повлияли на план?',
  'Где находится основная зона ограничений?',
  'Почему здесь кустарник, а не дерево?',
]

export function AIAssistant() {
  const jobId = useProjectStore((s) => s.jobId)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const [isFallback, setIsFallback] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const ask = async (q: string) => {
    if (!jobId || !q.trim()) return
    setLoading(true)
    setError(null)
    setAnswer(null)
    setIsFallback(false)
    try {
      const res = await askAI(jobId, q.trim())
      setAnswer(res.answer)
      setIsFallback(res.fallback)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка запроса к ИИ')
    } finally {
      setLoading(false)
    }
  }

  if (!jobId) {
    return (
      <div className="border-t border-slate-200 p-4 text-xs text-slate-400">
        Выполните расчёт для использования ИИ-ассистента
      </div>
    )
  }

  return (
    <div className="border-t border-slate-200 p-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-green-600" />
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">GREEN PLANNER AI</h4>
      </div>
      <p className="mt-1 text-[10px] text-slate-400">ИИ-анализ на основе результатов инженерного расчёта</p>

      <div className="mt-3 flex flex-wrap gap-1">
        {QUICK_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => { setQuestion(q); ask(q) }}
            className="rounded-lg bg-slate-50 px-2 py-1 text-[10px] text-slate-600 hover:bg-green-50 hover:text-green-700"
          >
            {q}
          </button>
        ))}
      </div>

      <div className="mt-3 flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask(question)}
          placeholder="Почему здесь нет деревьев?"
          className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-xs"
        />
        <Button size="sm" onClick={() => ask(question)} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
      </div>

      {loading && (
        <p className="mt-3 text-xs text-slate-500">Анализ ограничений участка…</p>
      )}

      {answer && (
        <div className="mt-3 space-y-2">
          {isFallback && (
            <p className="text-xs text-amber-600">ИИ недоступен — только детерминированные данные</p>
          )}
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm leading-relaxed text-slate-700">
            {answer}
          </div>
        </div>
      )}

      {error && (
        <p className="mt-2 text-xs text-red-600">{error}</p>
      )}
    </div>
  )
}
