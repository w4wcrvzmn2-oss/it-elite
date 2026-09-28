import { API_BASE } from '../lib/utils'

export function exportUrl(jobId: string, type: 'csv' | 'constraints' | 'summary' | 'pdf' | 'zip'): string {
  const paths = {
    csv: `/api/export/${jobId}/csv`,
    constraints: `/api/export/${jobId}/constraints`,
    summary: `/api/export/${jobId}/summary`,
    pdf: `/api/export/${jobId}/pdf`,
    zip: `/api/export/${jobId}/zip`,
  }
  return `${API_BASE}${paths[type]}`
}
