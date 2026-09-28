import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Cloud, FileUp, FolderOpen, Leaf, Plus, Sparkles, Upload, X } from 'lucide-react'
import { checkHealth, type MapAreaBBox, type MapAreaPreview } from '../api/client'
import { MoscowMapPicker } from '../components/map/MoscowMapPicker'
import { WorkspaceHeader } from '../components/layout/AppLayout'
import { useAnalyze } from '../hooks/useAnalyze'
import { useProjectStore } from '../stores/projectStore'
import { ProcessingStepper } from '../components/ui/Stepper'

export function Dashboard() {
  const navigate = useNavigate()
  const fileRef = useRef<HTMLInputElement>(null)
  const { runDemo, runRealisticDemo, runUpload, runFromMapArea } = useAnalyze()
  const jobStatus = useProjectStore((s) => s.jobStatus)
  const backendAvailable = useProjectStore((s) => s.backendAvailable)
  const setBackendAvailable = useProjectStore((s) => s.setBackendAvailable)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hover, setHover] = useState(false)
  const [uploadOpen, setUploadOpen] = useState(false)

  useEffect(() => {
    checkHealth()
      .then(() => setBackendAvailable(true))
      .catch(() => setBackendAvailable(false))
  }, [setBackendAvailable])

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.dxf')) {
      setError('Поддерживаются только файлы DXF')
      return
    }
    setError(null)
    setProcessing(true)
    try {
      await runUpload(file)
      navigate('/project/map')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить файл')
    } finally {
      setProcessing(false)
    }
  }, [runUpload, navigate])

  const run = useCallback(async (fn: () => Promise<void>, fallback: string) => {
    setError(null)
    setProcessing(true)
    try {
      await fn()
      navigate('/project/map')
    } catch (e) {
      setError(e instanceof Error ? e.message : fallback)
    } finally {
      setProcessing(false)
    }
  }, [navigate])

  const handleMapArea = useCallback(async (bbox: MapAreaBBox, _preview: MapAreaPreview | null) => {
    await run(() => runFromMapArea(bbox), 'Не удалось рассчитать участок с карты')
  }, [run, runFromMapArea])

  return (
    <div className="flex h-screen overflow-hidden bg-forest-950 text-mist-50">
      <aside className="flex w-[272px] shrink-0 flex-col border-r border-white/[0.05] bg-forest-900">
        <div className="px-5 pb-4 pt-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-leaf/20 bg-leaf/15 shadow-glow">
              <Leaf size={20} className="text-leaf" />
            </div>
            <div>
              <p className="text-[15px] font-extrabold leading-none tracking-tight">LandDesign</p>
              <p className="mt-1 text-[11px] text-mist-500">AI-озеленение городов</p>
            </div>
          </div>
        </div>
        <div className="space-y-2 px-4">
          <button className="btn-primary w-full py-2.5" onClick={() => setUploadOpen((open) => !open)}>
            <Plus size={16} />
            Новый проект
          </button>
          <div className="grid grid-cols-2 gap-2">
            <button className="btn-ghost py-2 text-xs" onClick={() => run(runRealisticDemo, 'Не удалось запустить демо')} disabled={backendAvailable === false}>
              <Sparkles size={13} />
              Примеры
            </button>
            <button className="btn-ghost py-2 text-xs" onClick={() => setUploadOpen(true)}>
              <Upload size={13} />
              Импорт
            </button>
          </div>
        </div>
        <div className="mt-4 flex-1 overflow-y-auto px-4">
          {uploadOpen && (
            <div className="animate-rise rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
              <div className="mb-2 flex items-start justify-between gap-2">
                <div>
                  <p className="label-caps">Создание проекта</p>
                  <h2 className="mt-1 text-base font-extrabold tracking-tight">Загрузите территорию</h2>
                </div>
                <button
                  onClick={() => setUploadOpen(false)}
                  className="rounded-lg p-1 text-mist-400 hover:bg-white/[0.06] hover:text-mist-50"
                  aria-label="Закрыть"
                >
                  <X size={16} />
                </button>
              </div>
              <p className="text-xs leading-relaxed text-mist-400">
                Импортируйте чертёж. Участок на карте выделяется отдельно, двумя кликами.
              </p>
              <button
                onDragOver={(e) => { e.preventDefault(); setHover(true) }}
                onDragLeave={() => setHover(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setHover(false)
                  const file = e.dataTransfer.files[0]
                  if (file) handleFile(file)
                }}
                onClick={() => fileRef.current?.click()}
                className={`mt-4 w-full rounded-2xl border border-dashed px-3 py-5 text-center transition-all ${
                  hover ? 'border-leaf bg-leaf/10' : 'border-white/15 bg-white/[0.03] hover:border-leaf/40 hover:bg-leaf/5'
                }`}
              >
                <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-leaf/15">
                  <Upload size={18} className="text-leaf" />
                </div>
                <p className="text-sm font-semibold">Перетащите файл сюда</p>
                <p className="mt-1 text-[11px] text-mist-500">или нажмите, чтобы выбрать с диска</p>
              </button>
              <div className="mt-3 grid grid-cols-3 gap-2">
                <button className="btn-ghost py-2 text-xs" onClick={() => fileRef.current?.click()}><FileUp size={14} />Файл</button>
                <button className="btn-ghost py-2 text-xs" onClick={() => run(runRealisticDemo, 'Не удалось запустить демо')}><Cloud size={14} />Пример</button>
                <button className="btn-ghost py-2 text-xs" onClick={() => run(runDemo, 'Не удалось запустить демо')}><FolderOpen size={14} />Демо</button>
              </div>
              {backendAvailable === false && (
                <p className="mt-3 text-xs text-accent-red">Сервер недоступен. Запустите API на порту 8000.</p>
              )}
              {error && <p className="mt-3 text-xs text-accent-red">{error}</p>}
            </div>
          )}
          {!uploadOpen && (
            <button
              className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-[13px] text-mist-400 transition-colors hover:bg-white/[0.04] hover:text-mist-50"
              onClick={() => run(runDemo, 'Не удалось запустить демо')}
              disabled={backendAvailable === false}
            >
              <FolderOpen size={15} />
              Показать демо
            </button>
          )}
        </div>
        <div className="border-t border-white/[0.05] p-4">
          <p className="px-3 text-[11px] text-mist-500">DXF · карта Москвы</p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <WorkspaceHeader projectName={null} />
        <div className="relative flex-1 overflow-hidden px-3 pb-3 pt-0">
          <div className="relative h-full overflow-hidden rounded-2xl border border-leaf/10 shadow-[inset_0_0_90px_rgba(61,220,132,0.07)]">
            <MoscowMapPicker
              onAnalyze={handleMapArea}
              disabled={backendAvailable === false || processing}
              bare
            />
          </div>
        </div>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept=".dxf"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
      />

      {processing && (
        <div className="animate-fade fixed inset-0 z-[2000] flex items-center justify-center bg-forest-950/70 p-6 backdrop-blur-md">
          <div className="glass-panel w-full max-w-md rounded-[24px] p-8">
            <ProcessingStepper progress={jobStatus?.progress ?? 5} stage={jobStatus?.stage ?? 'Запуск анализа…'} />
          </div>
        </div>
      )}
    </div>
  )
}
