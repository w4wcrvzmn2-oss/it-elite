import { useProjectStore } from '../stores/projectStore'
import { TopBar } from '../components/layout/AppLayout'
import { Card } from '../components/ui/Card'
import { AIStatus } from '../components/ai/AIStatus'

export function SettingsPage() {
  const parameters = useProjectStore((s) => s.parameters)
  const setParameters = useProjectStore((s) => s.setParameters)

  return (
    <>
      <TopBar title="Настройки" />
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-2xl space-y-6">
          <AIStatus />

          <Card className="p-6">
            <h3 className="text-sm font-semibold text-slate-900">Параметры озеленения</h3>
            <p className="mt-1 text-xs text-slate-500">Изменения применяются при следующем расчёте</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {[
                { key: 'tree_spacing' as const, label: 'Шаг деревьев (м)' },
                { key: 'shrub_spacing' as const, label: 'Шаг кустарников (м)' },
                { key: 'communication_buffer' as const, label: 'Буфер коммуникаций (м)' },
                { key: 'tree_max_count' as const, label: 'Макс. деревьев' },
                { key: 'shrub_max_count' as const, label: 'Макс. кустарников' },
                { key: 'tree_target_density' as const, label: 'Плотность деревьев / 1000 м²' },
              ].map(({ key, label }) => (
                <div key={key}>
                  <label className="text-xs text-slate-500">{label}</label>
                  <input
                    type="number"
                    step="0.1"
                    value={parameters[key] ?? ''}
                    onChange={(e) => setParameters({ [key]: e.target.value ? Number(e.target.value) : undefined })}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                    placeholder="По умолчанию"
                  />
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-sm font-semibold text-slate-900">Нормативные правила</h3>
            <p className="mt-2 text-sm text-slate-500">
              Нормативные документы и пункты доступны только для чтения.
              Пункты TODO_VERIFY требуют экспертной верификации.
            </p>
            <div className="mt-4 space-y-2 text-sm text-slate-600">
              <p>743-ПП — расстояния до коммуникаций (TODO_VERIFY)</p>
              <p>СП 42.13330.2016 — расстояния до зданий, шаг посадок (TODO_VERIFY)</p>
              <p>623-ПП — расстояния до дорог (TODO_VERIFY)</p>
              <p>МГСН — дополнительные требования (TODO_VERIFY)</p>
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
