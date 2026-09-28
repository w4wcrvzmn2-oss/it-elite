import { API_BASE } from '../lib/utils'
import type {
  AIAskResponse,
  AIExplanation,
  AIReport,
  AIStatus,
  AISiteSummary,
  ScenarioComparisonAI,
  SitePassport,
} from '../types/ai'

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getAIStatus(): Promise<AIStatus> {
  const res = await fetch(`${API_BASE}/api/ai/status`)
  if (!res.ok) throw new Error('Не удалось получить статус ИИ')
  return res.json()
}

export async function explainPlanting(jobId: string, plantingId: string): Promise<AIExplanation> {
  return post('/api/ai/explain-planting', { job_id: jobId, planting_id: plantingId })
}

export async function generateSiteSummary(jobId: string): Promise<AISiteSummary> {
  return post('/api/ai/site-summary', { job_id: jobId })
}

export async function askAI(jobId: string, question: string): Promise<AIAskResponse> {
  return post('/api/ai/ask', { job_id: jobId, question })
}

export async function generateAIReport(jobId: string): Promise<AIReport> {
  return post('/api/ai/report', { job_id: jobId })
}

export async function compareScenariosAI(jobId: string): Promise<ScenarioComparisonAI> {
  return post('/api/ai/compare-scenarios', { job_id: jobId })
}

export async function generatePassport(jobId: string): Promise<SitePassport> {
  return post('/api/ai/passport', { job_id: jobId })
}

export async function whyNotHere(jobId: string, x: number, y: number): Promise<{
  title: string
  reasons: string[]
  verification_notes: string[]
}> {
  return post('/api/ai/why-not', { job_id: jobId, x, y })
}
