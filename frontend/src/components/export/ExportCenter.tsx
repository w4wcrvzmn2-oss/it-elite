import { useState } from 'react'
import { Download, Package } from 'lucide-react'
import { exportUrl } from '../../api/export'
import { downloadUrl } from '../../api/client'
import { Button } from '../ui/Button'

const ITEMS = (jobId: string) => [
  { href: downloadUrl(jobId, 'dxf'), label: 'Скачать DXF' },
  { href: downloadUrl(jobId, 'interpretation'), label: 'Скачать JSON интерпретации' },
  { href: exportUrl(jobId, 'csv'), label: 'Скачать CSV посадок' },
  { href: exportUrl(jobId, 'summary'), label: 'Скачать Markdown отчёт' },
  { href: exportUrl(jobId, 'pdf'), label: 'Скачать PDF отчёт' },
  { href: exportUrl(jobId, 'zip'), label: 'Скачать ZIP проекта' },
]

export function ExportCenter({ jobId }: { jobId: string }) {
  const [open, setOpen] = useState(false)

  if (!open) {
    return (
      <Button variant="secondary" size="sm" onClick={() => setOpen(true)}>
        <Download className="h-4 w-4" />
        Экспорт
      </Button>
    )
  }

  return (
    <div className="absolute right-0 top-full z-50 mt-2 w-72 rounded-xl border border-slate-200 bg-white p-4 shadow-lg">
      <p className="text-xs font-semibold uppercase text-slate-500">Экспорт проекта</p>
      <div className="mt-3 space-y-2">
        {ITEMS(jobId).map(({ href, label }) => (
          <a
            key={label}
            href={href}
            className="block rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-green-50 hover:text-green-700"
          >
            {label}
          </a>
        ))}
      </div>
      <a href={exportUrl(jobId, 'zip')} className="mt-3 block">
        <Button className="w-full" size="sm">
          <Package className="h-4 w-4" />
          Скачать весь проект
        </Button>
      </a>
      <button type="button" onClick={() => setOpen(false)} className="mt-2 w-full text-xs text-slate-400 hover:text-slate-600">
        Закрыть
      </button>
    </div>
  )
}
