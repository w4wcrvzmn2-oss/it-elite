import { API_BASE } from '../lib/utils'

export interface ScenarioItem {
  id: string
  name: string
  description: string
  status: string
  tree_count: number
  shrub_count: number
  planting_count: number
  allowed_area_m2: number
  density_per_1000m2: number
  rejected_points: number
  processing_time_sec: number
}

export async function generateScenarios(jobId: string): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/scenarios/${jobId}/generate`, { method: 'POST' })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getScenarios(jobId: string): Promise<{
  status: string
  scenarios: ScenarioItem[]
  comparison: { rows: { metric: string; values: Record<string, number> }[]; scenarios: { id: string; name: string }[] }
}> {
  const res = await fetch(`${API_BASE}/api/scenarios/${jobId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
