export interface AIExplanation {
  title: string
  summary: string
  reasons: string[]
  constraints: string[]
  regulatory_notes: string[]
  verification_notes: string[]
  ai_generated: boolean
  fallback: boolean
}

export interface AISiteSummary {
  title: string
  summary: string
  key_metrics: string[]
  restrictions_overview: string
  planting_overview: string
  ai_generated: boolean
  fallback: boolean
}

export interface AIAskResponse {
  answer: string
  ai_generated: boolean
  fallback: boolean
}

export interface AIReportSection {
  title: string
  content: string
}

export interface AIReport {
  title: string
  overview: string
  sections: AIReportSection[]
  regulatory_notes: string[]
  verification_notes: string[]
  ai_generated: boolean
  fallback: boolean
}

export interface AIStatus {
  enabled: boolean
  available: boolean
  model: string | null
  message: string
  last_latency_sec?: number | null
  last_tokens?: number | null
  last_error?: string | null
}

export interface ScenarioComparisonAI {
  summary: string
  scenario_summaries: { id: string; summary: string }[]
  differences: string[]
  metrics_notes: string[]
  verification_notes: string[]
  ai_generated: boolean
  fallback: boolean
}

export interface SitePassport {
  title: string
  sections: AIReportSection[]
  regulatory_notes: string[]
  verification_notes: string[]
  executive_summary: string
  ai_generated: boolean
  fallback: boolean
}
