import { API_BASE } from '../lib/utils'

export interface VisualizationItem {
  id: string
  title: string
  filename: string
  created_at: string
  model: string
  badge: string
  ai_generated?: boolean
  kind?: 'plan' | 'ai'
}

export async function generateVisualizations(jobId: string): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/visualizations/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getVisualizations(jobId: string): Promise<{
  status: string
  visualizations: VisualizationItem[]
}> {
  const res = await fetch(`${API_BASE}/api/visualizations/${jobId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function visualizationImageUrl(jobId: string, vizId: string): string {
  return `${API_BASE}/api/visualizations/${jobId}/${vizId}/image`
}
