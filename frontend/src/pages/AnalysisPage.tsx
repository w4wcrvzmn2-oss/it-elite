import { BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts'
import { useProjectStore } from '../stores/projectStore'
import { TopBar } from '../components/layout/AppLayout'
import { Card } from '../components/ui/Card'
import { formatNumber } from '../lib/utils'

const COLORS = ['#16A34A', '#FEE2E2', '#2563EB', '#4ADE80']

export function AnalysisPage() {
  const stats = useProjectStore((s) => s.statistics)
  const plantings = useProjectStore((s) => s.plantings)

  if (!stats) {
    return (
      <>
        <TopBar title="Аналитика" />
        <div className="flex flex-1 items-center justify-center text-sm text-slate-500">Нет данных для анализа</div>
      </>
    )
  }

  const areaData = [
    { name: 'Разрешено', value: stats.allowed_area_m2 },
    { name: 'Ограничено', value: stats.forbidden_area_m2 },
  ]

  const typeData = [
    { name: 'Деревья', value: stats.tree_count },
    { name: 'Кустарники', value: stats.shrub_count },
  ]

  const constraintCounts = { communication: 0, building: 0, road: 0, spacing: 0 }
  for (const p of plantings) {
    for (const c of p.checks) {
      if (c.status === 'passed') {
        if (c.rule.includes('communication')) constraintCounts.communication++
        else if (c.rule.includes('building')) constraintCounts.building++
        else if (c.rule.includes('road')) constraintCounts.road++
        else if (c.rule === 'minimum_spacing') constraintCounts.spacing++
      }
    }
  }

  const constraintData = [
    { name: 'Коммуникации', value: constraintCounts.communication },
    { name: 'Здания', value: constraintCounts.building },
    { name: 'Дороги', value: constraintCounts.road },
    { name: 'Шаг', value: constraintCounts.spacing },
  ]

  return (
    <>
      <TopBar title="Аналитика" />
      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid gap-6 md:grid-cols-2">
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-slate-900">Распределение площади</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={areaData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {areaData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                </Pie>
                <Tooltip formatter={(v) => formatNumber(Number(v)) + ' м²'} />
              </PieChart>
            </ResponsiveContainer>
          </Card>

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-slate-900">Посадки по типу</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={typeData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#16A34A" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-slate-900">Пройденные проверки</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={constraintData}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#2563EB" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-slate-900">Плотность посадок</h3>
            <div className="mt-8 text-center">
              <p className="text-4xl font-bold tabular-nums text-green-600">
                {stats.density_per_1000m2.toFixed(1)}
              </p>
              <p className="mt-1 text-sm text-slate-500">посадок на 1000 м²</p>
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
