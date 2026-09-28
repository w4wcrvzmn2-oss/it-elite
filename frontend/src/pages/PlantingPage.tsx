import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useProjectStore } from '../stores/projectStore'
import { TopBar } from '../components/layout/AppLayout'
import { formatNumber } from '../lib/utils'
import type { Planting } from '../types/api'

export function PlantingPage() {
  const plantings = useProjectStore((s) => s.plantings)
  const selectPlanting = useProjectStore((s) => s.selectPlanting)
  const [tab, setTab] = useState<'all' | 'tree' | 'shrub'>('all')
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    let list = plantings
    if (tab === 'tree') list = list.filter((p) => p.type === 'tree')
    if (tab === 'shrub') list = list.filter((p) => p.type === 'shrub')
    if (search) list = list.filter((p) => p.id.toLowerCase().includes(search.toLowerCase()))
    return list
  }, [plantings, tab, search])

  const getCommDist = (p: Planting) => {
    const c = p.checks.find((x) => x.rule === 'communication_distance')
    return c?.value != null ? `${c.value.toFixed(2)} м` : '—'
  }

  const getSpacing = (p: Planting) => {
    const c = p.checks.find((x) => x.rule === 'minimum_spacing')
    return c?.value != null ? `${c.value.toFixed(2)} м` : '—'
  }

  const normStatus = (p: Planting) =>
    p.checks.some((c) => c.clause === 'TODO_VERIFY') ? 'TODO_VERIFY' : 'OK'

  return (
    <>
      <TopBar title="Озеленение" />
      <div className="flex-1 overflow-y-auto p-6">
        <p className="text-sm text-slate-500">{formatNumber(plantings.length)} предложенных посадок</p>

        <div className="mt-4 flex items-center gap-4">
          <div className="flex rounded-xl border border-slate-200 bg-white p-1">
            {(['all', 'tree', 'shrub'] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={`rounded-lg px-4 py-1.5 text-sm ${tab === t ? 'bg-green-50 font-medium text-green-700' : 'text-slate-600'}`}
              >
                {t === 'all' ? 'Все' : t === 'tree' ? 'Деревья' : 'Кустарники'}
              </button>
            ))}
          </div>
          <input
            type="search"
            placeholder="Поиск по ID…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="rounded-xl border border-slate-200 px-3 py-1.5 text-sm"
          />
        </div>

        <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <div className="max-h-[calc(100vh-220px)] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-slate-50 text-left text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Тип</th>
                  <th className="px-4 py-3">X</th>
                  <th className="px-4 py-3">Y</th>
                  <th className="px-4 py-3">Статус</th>
                  <th className="px-4 py-3">Коммуникация</th>
                  <th className="px-4 py-3">Шаг</th>
                  <th className="px-4 py-3">Норматив</th>
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 500).map((p) => (
                  <tr
                    key={p.id}
                    onClick={() => selectPlanting(p)}
                    className="cursor-pointer border-t border-slate-100 hover:bg-green-50/50"
                  >
                    <td className="px-4 py-2 font-mono text-xs">{p.id.toUpperCase()}</td>
                    <td className="px-4 py-2">{p.type === 'tree' ? 'Дерево' : 'Кустарник'}</td>
                    <td className="px-4 py-2 tabular-nums">{p.x.toFixed(2)}</td>
                    <td className="px-4 py-2 tabular-nums">{p.y.toFixed(2)}</td>
                    <td className="px-4 py-2"><span className="text-green-600">Допустимо</span></td>
                    <td className="px-4 py-2 tabular-nums">{getCommDist(p)}</td>
                    <td className="px-4 py-2 tabular-nums">{getSpacing(p)}</td>
                    <td className="px-4 py-2 text-xs text-amber-700">{normStatus(p)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length > 500 && (
              <p className="p-4 text-center text-xs text-slate-400">
                Показаны первые 500 из {filtered.length} — используйте поиск
              </p>
            )}
          </div>
        </div>
        <p className="mt-4 text-xs text-slate-500">
          <Link to="/project/map" className="text-green-600 hover:underline">Открыть на карте</Link>
        </p>
      </div>
    </>
  )
}
