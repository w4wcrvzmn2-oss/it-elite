export interface UploadResponse {
  file_id: string
  filename: string
  size: number
  status: string
}

export interface AnalyzeConfig {
  tree_spacing?: number
  shrub_spacing?: number
  communication_buffer?: number
  tree_max_count?: number | null
  shrub_max_count?: number | null
  tree_target_density?: number | null
  shrub_target_density?: number | null
}

export interface AnalyzeResponse {
  job_id: string
  status: string
}

export interface JobStatus {
  job_id: string
  status: 'queued' | 'processing' | 'completed' | 'error'
  progress: number
  stage: string
  error?: string | null
  filename?: string | null
}

export interface SiteStatistics {
  site_area_m2: number
  forbidden_area_m2: number
  allowed_area_m2: number
  planting_count: number
  density_per_1000m2: number
  tree_count: number
  shrub_count: number
  communications: number
  processing_time_sec: number
  planting_config: Record<string, PlantingConfigEntry>
  rules_applied: Record<string, unknown>[]
  normative_verification_required: boolean
}

export interface PlantingConfigEntry {
  min_spacing: number
  max_count: number | null
  target_density: number | null
  enabled: boolean
  accepted_count?: number
}

export interface RuleCheck {
  rule: string
  value: number | null
  required: number
  status: string
  regulation: string
  clause: string
  description: string
}

export interface Planting {
  id: string
  type: string
  x: number
  y: number
  status: string
  score: number
  checks: RuleCheck[]
  distances: Record<string, number | null>
  explanation: string
}

export interface InterpretationResponse {
  plantings: Planting[]
  rejected_count: number
  rules_applied: Record<string, unknown>[]
  summary: Record<string, unknown>
}

export interface GeometryFeature {
  type: string
  geometry: GeoJSON.Geometry
  properties: Record<string, unknown>
}

export interface GeometryResponse {
  bounds: number[]
  site: GeometryFeature[]
  communications: GeometryFeature[]
  buildings: GeometryFeature[]
  roads: GeometryFeature[]
  restricted_zones: GeometryFeature[]
  allowed_area: GeometryFeature[]
  trees: GeometryFeature[]
  shrubs: GeometryFeature[]
}

export interface LayerVisibility {
  basePlan: boolean
  communications: boolean
  buildings: boolean
  roads: boolean
  restrictedZones: boolean
  allowedArea: boolean
  trees: boolean
  shrubs: boolean
}

export const DEFAULT_LAYERS: LayerVisibility = {
  basePlan: true,
  communications: true,
  buildings: true,
  roads: true,
  restrictedZones: true,
  allowedArea: true,
  trees: true,
  shrubs: true,
}
