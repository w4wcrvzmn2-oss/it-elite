import { useEffect, useMemo, useRef } from 'react'
import L from 'leaflet'
import { MapContainer, useMap, ZoomControl } from 'react-leaflet'
import type { GeometryFeature, GeometryResponse, LayerVisibility, Planting } from '../../types/api'

export function flipY(y: number, maxY: number, minY: number): number {
  return maxY + minY - y
}

function transformCoords(
  coords: number[] | number[][] | number[][][],
  maxY: number,
  minY: number,
): number[] | number[][] | number[][][] {
  if (typeof coords[0] === 'number') {
    const [x, y] = coords as number[]
    return [flipY(y, maxY, minY), x]
  }
  return (coords as number[][] | number[][][]).map((c) =>
    transformCoords(c as number[] | number[][] | number[][][], maxY, minY),
  ) as number[][] | number[][][]
}

const STYLES = {
  site: { color: '#334155', weight: 3, fill: false, dashArray: '8 4', opacity: 1 },
  communication: { color: '#1D4ED8', weight: 3, opacity: 0.9 },
  building: { color: '#57534E', weight: 2, fillColor: '#A8A29E', fillOpacity: 0.45 },
  road: { color: '#64748B', weight: 5, opacity: 0.85, lineCap: 'round' as const },
  restricted: { color: '#EF4444', weight: 1, fillColor: '#FECACA', fillOpacity: 0.35, opacity: 0.6 },
  allowed: { color: '#22C55E', weight: 1, fillColor: '#BBF7D0', fillOpacity: 0.25, opacity: 0.5 },
}

function addGeoJsonLayer(
  map: L.Map,
  features: GeometryFeature[],
  style: L.PathOptions,
  maxY: number,
  minY: number,
): L.LayerGroup {
  const group = L.layerGroup()
  for (const f of features) {
    const geom = f.geometry as GeoJSON.Geometry
    const coords = 'coordinates' in geom ? geom.coordinates : []
    const transformed = { ...geom, coordinates: transformCoords(coords as never, maxY, minY) }
    const layer = L.geoJSON(transformed as GeoJSON.GeoJsonObject, {
      style: () => style,
      pointToLayer: (_f, latlng) =>
        L.circleMarker(latlng, { radius: 5, color: style.color, fillColor: style.fillColor, fillOpacity: 0.8 }),
    })
    group.addLayer(layer)
  }
  group.addTo(map)
  return group
}

function GridBackground({ bounds, maxY, minY }: { bounds: number[]; maxY: number; minY: number }) {
  const map = useMap()
  useEffect(() => {
    if (bounds.length !== 4) return
    const [minX, , maxX] = bounds
    const step = Math.max((maxX - minX) / 20, 5)
    const lines: L.Layer[] = []

    for (let x = minX; x <= maxX; x += step) {
      const line = L.polyline(
        [[flipY(bounds[1], maxY, minY), x], [flipY(bounds[3], maxY, minY), x]],
        { color: '#CBD5E1', weight: 0.5, opacity: 0.4, interactive: false },
      )
      line.addTo(map)
      lines.push(line)
    }
    for (let y = bounds[1]; y <= bounds[3]; y += step) {
      const line = L.polyline(
        [[flipY(y, maxY, minY), minX], [flipY(y, maxY, minY), maxX]],
        { color: '#CBD5E1', weight: 0.5, opacity: 0.4, interactive: false },
      )
      line.addTo(map)
      lines.push(line)
    }

    return () => lines.forEach((l) => map.removeLayer(l))
  }, [map, bounds, maxY, minY])
  return null
}

function siteFrame(geometry: GeometryResponse, fallback: number[]): number[] {
  const ring = geometry.site[0]?.geometry
  const coords = ring && 'coordinates' in ring ? ring.coordinates : null
  const points = Array.isArray(coords) ? (coords[0] as number[][]) : null
  if (!points?.length) return fallback
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity
  for (const pt of points) {
    if (!Array.isArray(pt) || pt.length < 2) continue
    minX = Math.min(minX, pt[0])
    minY = Math.min(minY, pt[1])
    maxX = Math.max(maxX, pt[0])
    maxY = Math.max(maxY, pt[1])
  }
  if (!Number.isFinite(minX)) return fallback
  const pad = Math.max(maxX - minX, maxY - minY) * 0.04
  return [minX - pad, minY - pad, maxX + pad, maxY + pad]
}

function FitBounds({
  bounds,
  maxY,
  minY,
  trigger,
}: {
  bounds: number[]
  maxY: number
  minY: number
  trigger: number
}) {
  const map = useMap()
  useEffect(() => {
    if (bounds.length === 4) {
      const sw = L.latLng(flipY(bounds[1], maxY, minY), bounds[0])
      const ne = L.latLng(flipY(bounds[3], maxY, minY), bounds[2])
      map.fitBounds(L.latLngBounds(sw, ne), { padding: [48, 48], maxZoom: 2, animate: true })
    }
  }, [map, bounds, maxY, minY, trigger])
  return null
}

function DistanceOverlay({
  planting,
  maxY,
  minY,
}: {
  planting: Planting
  maxY: number
  minY: number
}) {
  const map = useMap()
  useEffect(() => {
    const latlng = L.latLng(flipY(planting.y, maxY, minY), planting.x)
    const rings: L.Layer[] = []
    const colors: Record<string, string> = {
      communication_distance: '#2563EB',
      building_distance: '#78716C',
      road_distance: '#64748B',
    }
    for (const check of planting.checks) {
      if (check.status !== 'passed' || !check.required) continue
      const color = colors[check.rule] || '#22C55E'
      const circle = L.circle(latlng, {
        radius: check.required,
        color,
        fill: false,
        dashArray: '4 4',
        weight: 1,
        opacity: 0.6,
        interactive: false,
      }).addTo(map)
      rings.push(circle)
    }
    return () => rings.forEach((r) => map.removeLayer(r))
  }, [map, planting, maxY, minY])
  return null
}

function MapContent({
  geometry,
  plantings,
  layers,
  selectedId,
  selectedPlanting,
  onSelectPlanting,
  onMapClick,
  fitTrigger,
}: {
  geometry: GeometryResponse
  plantings: Planting[]
  layers: LayerVisibility
  selectedId: string | null
  selectedPlanting: Planting | null
  onSelectPlanting: (p: Planting) => void
  onMapClick?: (x: number, y: number) => void
  fitTrigger: number
}) {
  const map = useMap()
  const layersRef = useRef<L.LayerGroup[]>([])
  const plantingLayerRef = useRef<L.LayerGroup | null>(null)
  const highlightRef = useRef<L.Circle | null>(null)

  const bounds = geometry.bounds
  const frame = siteFrame(geometry, bounds)
  const minY = bounds[1]
  const maxY = bounds[3]

  useEffect(() => {
    layersRef.current.forEach((l) => map.removeLayer(l))
    layersRef.current = []

    // Draw order: allowed → restricted → infrastructure → site outline
    if (layers.allowedArea && geometry.allowed_area.length) {
      layersRef.current.push(addGeoJsonLayer(map, geometry.allowed_area, STYLES.allowed, maxY, minY))
    }
    if (layers.restrictedZones && geometry.restricted_zones.length) {
      layersRef.current.push(addGeoJsonLayer(map, geometry.restricted_zones, STYLES.restricted, maxY, minY))
    }
    if (layers.roads && geometry.roads.length) {
      layersRef.current.push(addGeoJsonLayer(map, geometry.roads, STYLES.road, maxY, minY))
    }
    if (layers.buildings && geometry.buildings.length) {
      layersRef.current.push(addGeoJsonLayer(map, geometry.buildings, STYLES.building, maxY, minY))
    }
    if (layers.communications && geometry.communications.length) {
      layersRef.current.push(addGeoJsonLayer(map, geometry.communications, STYLES.communication, maxY, minY))
    }
    if (layers.basePlan && geometry.site.length) {
      layersRef.current.push(addGeoJsonLayer(map, geometry.site, STYLES.site, maxY, minY))
    }

    return () => {
      layersRef.current.forEach((l) => map.removeLayer(l))
      layersRef.current = []
    }
  }, [map, geometry, layers, maxY, minY])

  useEffect(() => {
    if (plantingLayerRef.current) map.removeLayer(plantingLayerRef.current)
    if (highlightRef.current) map.removeLayer(highlightRef.current)

    const group = L.layerGroup()
    const canvasRenderer = L.canvas({ padding: 0.5 })

    const treePlantings = layers.trees ? plantings.filter((p) => p.type === 'tree') : []
    const shrubPlantings = layers.shrubs ? plantings.filter((p) => p.type === 'shrub') : []

    for (const p of shrubPlantings) {
      if (p.id === selectedId) continue
      const latlng = L.latLng(flipY(p.y, maxY, minY), p.x)
      L.circle(latlng, {
        radius: 0.6,
        color: '#86EFAC',
        fillColor: '#4ADE80',
        fillOpacity: 0.8,
        weight: 0.4,
        renderer: canvasRenderer,
      })
        .on('click', () => onSelectPlanting(p))
        .addTo(group)
    }

    for (const p of treePlantings) {
      if (p.id === selectedId) continue
      const latlng = L.latLng(flipY(p.y, maxY, minY), p.x)
      L.circle(latlng, {
        radius: 1.6,
        color: '#15803D',
        fillColor: '#22C55E',
        fillOpacity: 0.85,
        weight: 0.6,
        renderer: canvasRenderer,
      })
        .on('click', () => onSelectPlanting(p))
        .addTo(group)
    }

    if (selectedPlanting) {
      const latlng = L.latLng(flipY(selectedPlanting.y, maxY, minY), selectedPlanting.x)
      highlightRef.current = L.circle(latlng, {
        radius: selectedPlanting.type === 'tree' ? 4 : 2,
        color: '#15803D',
        fillColor: '#22C55E',
        fillOpacity: 0.95,
        weight: 3,
      }).addTo(map)

      L.circleMarker(latlng, {
        radius: selectedPlanting.type === 'tree' ? 10 : 6,
        color: '#FFFFFF',
        fillColor: '#16A34A',
        fillOpacity: 1,
        weight: 3,
      })
        .on('click', () => onSelectPlanting(selectedPlanting))
        .addTo(group)
    }

    group.addTo(map)
    plantingLayerRef.current = group

    return () => {
      if (plantingLayerRef.current) map.removeLayer(plantingLayerRef.current)
      if (highlightRef.current) map.removeLayer(highlightRef.current)
    }
  }, [map, plantings, layers.trees, layers.shrubs, selectedId, selectedPlanting, onSelectPlanting, maxY, minY])

  useEffect(() => {
    if (selectedPlanting && bounds.length === 4) {
      const latlng = L.latLng(flipY(selectedPlanting.y, maxY, minY), selectedPlanting.x)
      map.setView(latlng, Math.max(map.getZoom(), 1), { animate: true })
    }
  }, [selectedPlanting, map, maxY, minY, bounds])

  useEffect(() => {
    if (!onMapClick) return
    const handler = (e: L.LeafletMouseEvent) => {
      onMapClick(e.latlng.lng, flipY(e.latlng.lat, maxY, minY))
    }
    map.on('click', handler)
    return () => { map.off('click', handler) }
  }, [map, onMapClick, maxY, minY])

  return (
    <>
      <GridBackground bounds={frame} maxY={maxY} minY={minY} />
      <FitBounds bounds={frame} maxY={maxY} minY={minY} trigger={fitTrigger} />
      {selectedPlanting && <DistanceOverlay planting={selectedPlanting} maxY={maxY} minY={minY} />}
    </>
  )
}

export function SiteMap({
  geometry,
  plantings,
  layers,
  selectedId,
  selectedPlanting,
  onSelectPlanting,
  onMapClick,
  fitTrigger,
}: {
  geometry: GeometryResponse | null
  plantings: Planting[]
  layers: LayerVisibility
  selectedId: string | null
  selectedPlanting: Planting | null
  onSelectPlanting: (p: Planting) => void
  onMapClick?: (x: number, y: number) => void
  fitTrigger: number
}) {
  const center = useMemo((): [number, number] => {
    if (!geometry?.bounds?.length) return [0, 0]
    const [minX, minY, maxX, maxY] = geometry.bounds
    return [flipY((minY + maxY) / 2, maxY, minY), (minX + maxX) / 2]
  }, [geometry])

  if (!geometry) {
    return (
      <div className="flex h-full items-center justify-center bg-forest-950 text-sm text-mist-500">
        Геометрия не загружена
      </div>
    )
  }

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={center}
        zoom={0}
        minZoom={-2}
        maxZoom={6}
        crs={L.CRS.Simple}
        className="h-full w-full z-0"
        zoomControl={false}
        preferCanvas
      >
        <ZoomControl position="bottomright" />
        <MapContent
          geometry={geometry}
          plantings={plantings}
          layers={layers}
          selectedId={selectedId}
          selectedPlanting={selectedPlanting}
          onSelectPlanting={onSelectPlanting}
          onMapClick={onMapClick}
          fitTrigger={fitTrigger}
        />
      </MapContainer>
      <MapLegend />
    </div>
  )
}

function MapLegend() {
  const items = [
    { color: 'bg-green-700', label: 'Деревья' },
    { color: 'bg-green-300', label: 'Кустарники' },
    { color: 'bg-red-200', label: 'Ограничения' },
    { color: 'bg-green-100', label: 'Разрешено' },
    { color: 'bg-blue-600', label: 'Коммуникации' },
    { color: 'bg-slate-300', label: 'Подоснова' },
  ]
  return (
    <div className="glass-panel pointer-events-none absolute bottom-4 left-4 z-[1000] rounded-xl px-3 py-2">
      <p className="label-caps mb-1.5">Легенда</p>
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {items.map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
            <span className="text-[10px] text-mist-200">{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function MapControls({
  onFit,
  layers,
  onToggleLayer,
}: {
  onFit: () => void
  layers: LayerVisibility
  onToggleLayer: (key: keyof LayerVisibility) => void
}) {
  const layerLabels: { key: keyof LayerVisibility; label: string; color: string }[] = [
    { key: 'basePlan', label: 'Подоснова', color: 'border-slate-600' },
    { key: 'communications', label: 'Коммуникации', color: 'border-blue-600' },
    { key: 'buildings', label: 'Здания', color: 'border-stone-500' },
    { key: 'roads', label: 'Дороги', color: 'border-slate-400' },
    { key: 'restrictedZones', label: 'Ограничения', color: 'border-red-400' },
    { key: 'allowedArea', label: 'Разрешённая зона', color: 'border-green-400' },
    { key: 'trees', label: 'Деревья', color: 'border-green-600' },
    { key: 'shrubs', label: 'Кустарники', color: 'border-green-300' },
  ]

  return (
    <div className="absolute right-3 top-3 z-[1000] w-64 space-y-2">
      <div className="glass-panel rounded-2xl p-2">
        <button
          onClick={onFit}
          className="w-full rounded-xl px-3 py-2 text-left text-xs font-medium text-mist-200 hover:bg-leaf/10 hover:text-leaf-glow"
        >
          По размеру участка
        </button>
      </div>
      <div className="glass-panel animate-rise rounded-2xl p-4">
        <p className="mb-3 text-sm font-semibold text-mist-50">Слои карты</p>
        <div className="space-y-1.5">
          {layerLabels.map(({ key, label, color }) => (
            <label key={key} className="flex cursor-pointer items-center gap-2 rounded-xl px-1 py-1 text-[13px] text-mist-200">
              <input
                type="checkbox"
                checked={layers[key]}
                onChange={() => onToggleLayer(key)}
                className="rounded border-slate-300 text-green-600 focus:ring-green-500"
              />
              <span className={`h-0.5 w-3 border-t-2 ${color}`} />
              {label}
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}
