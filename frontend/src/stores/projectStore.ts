import { create } from 'zustand'
import type { AnalyzeConfig, GeometryResponse, JobStatus, LayerVisibility, Planting, SiteStatistics } from '../types/api'
import { DEFAULT_LAYERS } from '../types/api'

interface ProjectState {
  fileId: string | null
  filename: string | null
  jobId: string | null
  jobStatus: JobStatus | null
  statistics: SiteStatistics | null
  geometry: GeometryResponse | null
  plantings: Planting[]
  selectedPlanting: Planting | null
  layers: LayerVisibility
  parameters: AnalyzeConfig
  backendAvailable: boolean | null

  setFile: (fileId: string, filename: string) => void
  setJob: (jobId: string) => void
  setJobStatus: (status: JobStatus) => void
  setStatistics: (stats: SiteStatistics) => void
  setGeometry: (geometry: GeometryResponse) => void
  setPlantings: (plantings: Planting[]) => void
  selectPlanting: (planting: Planting | null) => void
  toggleLayer: (key: keyof LayerVisibility) => void
  setParameters: (params: Partial<AnalyzeConfig>) => void
  setBackendAvailable: (v: boolean) => void
  reset: () => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  fileId: null,
  filename: null,
  jobId: null,
  jobStatus: null,
  statistics: null,
  geometry: null,
  plantings: [],
  selectedPlanting: null,
  layers: { ...DEFAULT_LAYERS },
  parameters: {},
  backendAvailable: null,

  setFile: (fileId, filename) => set({ fileId, filename }),
  setJob: (jobId) => set({ jobId, jobStatus: null, statistics: null, geometry: null, plantings: [], selectedPlanting: null }),
  setJobStatus: (jobStatus) => set({ jobStatus }),
  setStatistics: (statistics) => set({ statistics }),
  setGeometry: (geometry) => set({ geometry }),
  setPlantings: (plantings) => set({ plantings }),
  selectPlanting: (selectedPlanting) => set({ selectedPlanting }),
  toggleLayer: (key) => set((s) => ({ layers: { ...s.layers, [key]: !s.layers[key] } })),
  setParameters: (params) => set((s) => ({ parameters: { ...s.parameters, ...params } })),
  setBackendAvailable: (backendAvailable) => set({ backendAvailable }),
  reset: () => set({
    fileId: null, filename: null, jobId: null, jobStatus: null,
    statistics: null, geometry: null, plantings: [], selectedPlanting: null,
    layers: { ...DEFAULT_LAYERS }, parameters: {},
  }),
}))
