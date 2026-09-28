import { API_BASE } from '../lib/utils'
import type {
  AnalyzeConfig,
  AnalyzeResponse,
  GeometryResponse,
  InterpretationResponse,
  JobStatus,
  SiteStatistics,
  UploadResponse,
} from '../types/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, options)
  if (!res.ok) {
    const body = await res.text()
    let message = body
    try {
      const parsed = JSON.parse(body) as { detail?: string }
      if (typeof parsed.detail === 'string') message = parsed.detail
    } catch {
      // leave raw body
    }
    throw new Error(message || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function checkHealth(): Promise<{ status: string }> {
  return request('/api/health')
}

export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  const url = `${API_BASE}/api/upload`
  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function uploadDemo(): Promise<UploadResponse> {
  return request('/api/demo/upload', { method: 'POST' })
}

export async function uploadRealisticDemo(): Promise<UploadResponse> {
  return request('/api/demo/upload-realistic', { method: 'POST' })
}

export async function analyze(
  fileId: string,
  config?: AnalyzeConfig,
  demo = false,
): Promise<AnalyzeResponse> {
  return request('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: fileId, demo, config }),
  })
}

export interface MapAreaBBox {
  south: number
  west: number
  north: number
  east: number
  label?: string
}

export interface MapAreaPreview {
  buildings: number
  roads: number
  width_m: number
  height_m: number
  message: string
}

export async function previewMapArea(bbox: MapAreaBBox): Promise<MapAreaPreview> {
  return request('/api/map/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...bbox, label: bbox.label ?? 'moscow_map' }),
  })
}

export async function analyzeFromMap(bbox: MapAreaBBox): Promise<AnalyzeResponse> {
  return request('/api/analyze/from-map', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...bbox, label: bbox.label ?? 'moscow_map' }),
  })
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return request(`/api/jobs/${jobId}`)
}

export async function getStatistics(jobId: string): Promise<SiteStatistics> {
  return request(`/api/jobs/${jobId}/statistics`)
}

export async function getGeometry(jobId: string): Promise<GeometryResponse> {
  return request(`/api/jobs/${jobId}/geometry`)
}

export async function getInterpretation(jobId: string): Promise<InterpretationResponse> {
  return request(`/api/jobs/${jobId}/interpretation`)
}

export function downloadUrl(jobId: string, type: 'dxf' | 'interpretation' | 'report'): string {
  const paths = {
    dxf: `/api/jobs/${jobId}/download/dxf`,
    interpretation: `/api/jobs/${jobId}/download/interpretation`,
    report: `/api/jobs/${jobId}/download/report`,
  }
  return `${API_BASE}${paths[type]}`
}
