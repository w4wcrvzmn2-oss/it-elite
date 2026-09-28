import { useCallback, useState } from 'react'
import { useProjectStore } from '../stores/projectStore'
import { TopBar } from '../components/layout/AppLayout'
import { SiteMap, MapControls } from '../components/map/SiteMap'
import { PlantingInspector } from '../components/inspector/PlantingInspector'
import { ExportCenter } from '../components/export/ExportCenter'
import { whyNotHere } from '../api/ai'

export function MapWorkspace() {
  const filename = useProjectStore((s) => s.filename)
  const geometry = useProjectStore((s) => s.geometry)
  const plantings = useProjectStore((s) => s.plantings)
  const selectedPlanting = useProjectStore((s) => s.selectedPlanting)
  const layers = useProjectStore((s) => s.layers)
  const toggleLayer = useProjectStore((s) => s.toggleLayer)
  const selectPlanting = useProjectStore((s) => s.selectPlanting)
  const jobId = useProjectStore((s) => s.jobId)
  const [fitTrigger, setFitTrigger] = useState(0)
  const [whyNot, setWhyNot] = useState<{ title: string; reasons: string[] } | null>(null)

  const handleMapClick = useCallback(async (x: number, y: number) => {
    if (!jobId) return
    setWhyNot(null)
    selectPlanting(null)
    try {
      const result = await whyNotHere(jobId, x, y)
      setWhyNot({ title: result.title, reasons: result.reasons })
    } catch {
      setWhyNot({
        title: 'Почему здесь нет посадки?',
        reasons: ['Недостаточно данных для объяснения этой точки.'],
      })
    }
  }, [jobId, selectPlanting])

  const handleSelectPlanting = useCallback((p: typeof selectedPlanting) => {
    setWhyNot(null)
    if (p) selectPlanting(p)
  }, [selectPlanting])

  return (
    <>
      <TopBar title={`Анализ участка / ${filename || 'Без названия'}`}>
        {jobId && <ExportCenter jobId={jobId} />}
      </TopBar>
      <div className="relative mx-3 mb-3 flex flex-1 overflow-hidden rounded-2xl border border-leaf/10 shadow-[inset_0_0_90px_rgba(61,220,132,0.07)]">
        <div className="relative min-w-0 flex-1">
          <SiteMap
            geometry={geometry}
            plantings={plantings}
            layers={layers}
            selectedId={selectedPlanting?.id ?? null}
            selectedPlanting={selectedPlanting}
            onSelectPlanting={handleSelectPlanting}
            onMapClick={handleMapClick}
            fitTrigger={fitTrigger}
          />
          <MapControls
            onFit={() => setFitTrigger((n) => n + 1)}
            layers={layers}
            onToggleLayer={toggleLayer}
          />
        </div>
        <aside className="glass-panel m-3 w-[340px] shrink-0 overflow-hidden rounded-2xl">
          <div className="border-b border-white/[0.06] px-4 py-3">
            <p className="label-caps">Инспектор</p>
          </div>
          <PlantingInspector planting={selectedPlanting} whyNot={whyNot} />
        </aside>
      </div>
    </>
  )
}
