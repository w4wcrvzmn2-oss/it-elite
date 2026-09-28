import { useCallback } from 'react'
import {
  analyze,
  analyzeFromMap,
  getGeometry,
  getInterpretation,
  getJobStatus,
  getStatistics,
  uploadDemo,
  uploadFile,
  uploadRealisticDemo,
  type MapAreaBBox,
} from '../api/client'
import { useProjectStore } from '../stores/projectStore'

export function useAnalyze() {
  const store = useProjectStore()

  const pollJob = useCallback(async (jobId: string) => {
    const maxAttempts = 360
    for (let i = 0; i < maxAttempts; i++) {
      const status = await getJobStatus(jobId)
      store.setJobStatus(status)
      if (status.status === 'completed') {
        const [stats, geometry, interpretation] = await Promise.all([
          getStatistics(jobId),
          getGeometry(jobId),
          getInterpretation(jobId),
        ])
        store.setStatistics(stats)
        store.setGeometry(geometry)
        store.setPlantings(interpretation.plantings)
        return true
      }
      if (status.status === 'error') {
        throw new Error(status.error || 'Ошибка обработки')
      }
      await new Promise((r) => setTimeout(r, 500))
    }
    throw new Error('Превышено время ожидания обработки')
  }, [store])

  const runDemo = useCallback(async () => {
    const upload = await uploadDemo()
    store.setFile(upload.file_id, upload.filename)
    const { job_id } = await analyze(upload.file_id, store.parameters, true)
    store.setJob(job_id)
    await pollJob(job_id)
  }, [store, pollJob])

  const runRealisticDemo = useCallback(async () => {
    const upload = await uploadRealisticDemo()
    store.setFile(upload.file_id, upload.filename)
    const { job_id } = await analyze(upload.file_id, store.parameters)
    store.setJob(job_id)
    await pollJob(job_id)
  }, [store, pollJob])

  const runUpload = useCallback(async (file: File) => {
    const upload = await uploadFile(file)
    store.setFile(upload.file_id, upload.filename)
    const { job_id } = await analyze(upload.file_id, store.parameters)
    store.setJob(job_id)
    await pollJob(job_id)
  }, [store, pollJob])

  const runFromMapArea = useCallback(async (bbox: MapAreaBBox) => {
    const { job_id } = await analyzeFromMap({ ...bbox, label: 'moscow_map' })
    store.setFile('map-area', `moscow_map_${Math.round(bbox.south * 1e4)}.dxf`)
    store.setJob(job_id)
    await pollJob(job_id)
  }, [store, pollJob])

  return { runDemo, runRealisticDemo, runUpload, runFromMapArea, pollJob }
}
