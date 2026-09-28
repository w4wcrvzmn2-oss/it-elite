import { useCallback, useMemo, useState } from 'react'
import { MapContainer, Rectangle, TileLayer, useMapEvents } from 'react-leaflet'
import type { LatLngBoundsExpression } from 'leaflet'
import { Loader2, MapPin } from 'lucide-react'
import { previewMapArea, type MapAreaBBox, type MapAreaPreview } from '../../api/client'
import { Button } from '../ui/Button'

const MOSCOW_CENTER: [number, number] = [55.7558, 37.6173]

function normalizeBBox(a: { lat: number; lng: number }, b: { lat: number; lng: number }): MapAreaBBox {
  return {
    south: Math.min(a.lat, b.lat),
    north: Math.max(a.lat, b.lat),
    west: Math.min(a.lng, b.lng),
    east: Math.max(a.lng, b.lng),
  }
}

function AreaClickHandler({
  corner,
  onCorner,
  onComplete,
}: {
  corner: { lat: number; lng: number } | null
  onCorner: (c: { lat: number; lng: number } | null) => void
  onComplete: (bbox: MapAreaBBox) => void
}) {
  useMapEvents({
    click(e) {
      if (!corner) {
        onCorner({ lat: e.latlng.lat, lng: e.latlng.lng })
      } else {
        onComplete(normalizeBBox(corner, { lat: e.latlng.lat, lng: e.latlng.lng }))
        onCorner(null)
      }
    },
  })
  return null
}

export function MoscowMapPicker({
  onAnalyze,
  disabled,
  bare = false,
}: {
  onAnalyze: (bbox: MapAreaBBox, preview: MapAreaPreview | null) => Promise<void>
  disabled?: boolean
  bare?: boolean
}) {
  const [corner, setCorner] = useState<{ lat: number; lng: number } | null>(null)
  const [bbox, setBbox] = useState<MapAreaBBox | null>(null)
  const [preview, setPreview] = useState<MapAreaPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const rectBounds = useMemo<LatLngBoundsExpression | null>(() => {
    if (!bbox) return null
    return [
      [bbox.south, bbox.west],
      [bbox.north, bbox.east],
    ]
  }, [bbox])

  const handleBBox = useCallback(async (next: MapAreaBBox) => {
    setBbox(next)
    setError(null)
    setLoading(true)
    try {
      setPreview(await previewMapArea(next))
    } catch (e) {
      setPreview(null)
      setError(e instanceof Error ? e.message : 'Не удалось получить данные OSM')
    } finally {
      setLoading(false)
    }
  }, [])

  const handleAnalyze = async () => {
    if (!bbox) return
    setLoading(true)
    setError(null)
    try {
      await onAnalyze(bbox, preview)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось запустить расчёт')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={bare ? 'map-skin-osm absolute inset-0' : 'rounded-2xl border border-white/[0.08] bg-forest-900 p-5'}>
      {!bare && (
        <div className="mb-3 flex items-center gap-2">
          <MapPin className="h-5 w-5 text-leaf" />
          <div>
            <p className="font-medium text-mist-50">Участок на карте Москвы</p>
            <p className="text-xs text-mist-500">
              OpenStreetMap · два клика по противоположным углам (40–450 м)
            </p>
          </div>
        </div>
      )}

      <div className={bare ? 'h-full w-full' : 'overflow-hidden rounded-xl border border-white/[0.08]'}>
        <MapContainer
          center={MOSCOW_CENTER}
          zoom={bare ? 14 : 16}
          className={bare ? 'h-full w-full' : 'h-72 w-full'}
          scrollWheelZoom
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <AreaClickHandler corner={corner} onCorner={setCorner} onComplete={handleBBox} />
          {rectBounds && (
            <Rectangle bounds={rectBounds} pathOptions={{ color: '#3ddc84', weight: 2, fillOpacity: 0.15 }} />
          )}
        </MapContainer>
      </div>

      <p className={`text-xs text-mist-400 ${bare ? 'pointer-events-none absolute bottom-4 left-4 z-[1000] rounded-xl bg-forest-950/70 px-3 py-2 backdrop-blur' : 'mt-2'}`}>
        {corner
          ? 'Кликните второй угол участка'
          : bbox
            ? `Выбрано: ${preview?.width_m ?? '—'}×${preview?.height_m ?? '—'} м`
            : 'Кликните первый угол участка на карте'}
      </p>

      {preview && (
        <p className={`text-xs text-mist-200 ${bare ? 'pointer-events-none absolute bottom-14 left-4 z-[1000]' : 'mt-1'}`}>
          OSM: зданий {preview.buildings}, дорог {preview.roads}. {preview.message}
        </p>
      )}

      {error && <p className={`text-xs text-accent-red ${bare ? 'absolute bottom-24 left-4 z-[1000] max-w-sm' : 'mt-2'}`}>{error}</p>}

      <Button
        className={bare ? 'absolute bottom-4 right-4 z-[1200] w-auto px-5 py-3' : 'mt-4 w-full'}
        disabled={disabled || !bbox || loading || (preview != null && preview.buildings === 0 && preview.roads === 0)}
        onClick={handleAnalyze}
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
        Рассчитать озеленение для участка
      </Button>
    </div>
  )
}
