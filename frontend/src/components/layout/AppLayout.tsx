import { useEffect, useRef, useState, type ReactNode } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  BarChart3, Bell, ChevronDown, FileText, FolderOpen, GitCompare, Image, Info,
  Leaf, LogOut, Map, MessageCircle, MoreVertical, Search, Settings, Shield, User, AlertTriangle,
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { ru } from '../../lib/i18n'
import { useProjectStore } from '../../stores/projectStore'

const navItems = [
  { to: '/project', icon: Map, label: ru.nav.overview },
  { to: '/project/map', icon: Map, label: ru.nav.siteAnalysis },
  { to: '/project/planting', icon: Leaf, label: ru.nav.planting },
  { to: '/project/constraints', icon: Shield, label: ru.nav.constraints },
  { to: '/project/analysis', icon: BarChart3, label: ru.nav.analytics },
  { to: '/project/scenarios', icon: GitCompare, label: ru.nav.scenarios },
  { to: '/project/visualization', icon: Image, label: ru.nav.visualization },
  { to: '/project/report', icon: FileText, label: ru.nav.report },
]

export function AppLayout() {
  const filename = useProjectStore((s) => s.filename)
  const navigate = useNavigate()

  return (
    <div className="flex h-screen overflow-hidden bg-forest-950 text-mist-50">
      <aside className="flex w-[272px] shrink-0 flex-col border-r border-white/[0.05] bg-forest-900">
        <div className="px-5 pb-4 pt-5">
          <button onClick={() => navigate('/')} className="flex items-center gap-3 text-left">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-leaf/20 bg-leaf/15 shadow-glow">
              <Leaf size={20} className="text-leaf" />
            </div>
            <div>
              <p className="text-[15px] font-extrabold leading-none tracking-tight">LandDesign</p>
              <p className="mt-1 text-[11px] text-mist-500">AI-озеленение городов</p>
            </div>
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-4">
          <p className="label-caps mb-2 px-1">Проект</p>
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/project'}
              className={({ isActive }) =>
                cn(
                  'flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-[13px] transition-colors',
                  isActive
                    ? 'border border-leaf/25 bg-leaf/10 font-semibold text-leaf-glow'
                    : 'border border-transparent text-mist-200 hover:bg-white/[0.04]',
                )
              }
            >
              <Icon size={15} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/[0.05] p-4">
          {filename && <p className="mb-2 truncate px-3 text-[11px] text-mist-500">{filename}</p>}
          <NavLink
            to="/project/settings"
            className={({ isActive }) =>
              cn(
                'flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-[13px] transition-colors',
                isActive ? 'bg-white/[0.05] text-mist-50' : 'text-mist-400 hover:bg-white/[0.04] hover:text-mist-50',
              )
            }
          >
            <Settings size={15} />
            Настройки
          </NavLink>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <WorkspaceHeader projectName={filename} />
        <main className="flex flex-1 flex-col overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export function WorkspaceHeader({ projectName }: { projectName: string | null }) {
  const [showMenu, setShowMenu] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const profileRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setShowMenu(false)
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) setShowProfile(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-6 px-5">
      <div className="min-w-0">
        <p className="label-caps">Рабочее пространство</p>
        <p className="mt-0.5 truncate text-[15px] font-semibold">
          {projectName ?? 'Выберите или создайте проект'}
        </p>
      </div>

      <div className="hidden max-w-md flex-1 md:flex">
        <label className="flex w-full items-center gap-2.5 rounded-xl border border-white/[0.06] bg-forest-800 px-3.5 py-2 transition-all focus-within:border-leaf/40 focus-within:shadow-glow">
          <Search size={15} className="shrink-0 text-mist-500" />
          <input
            type="search"
            placeholder="Поиск проектов, участков, слоёв..."
            className="w-full bg-transparent text-sm text-mist-50 outline-none placeholder:text-mist-500"
          />
          <kbd className="hidden rounded-md border border-white/10 px-1.5 py-0.5 font-mono text-[10px] text-mist-500 lg:inline">⌘K</kbd>
        </label>
      </div>

      <div className="flex items-center gap-2">
        <span className="hidden items-center rounded-lg border border-leaf/15 bg-leaf/10 px-2.5 py-1 text-[11px] font-semibold text-leaf sm:inline-flex">
          v1.0
        </span>
        <button className="relative rounded-xl p-2 text-mist-400 transition-colors hover:bg-white/[0.05] hover:text-mist-50">
          <Bell size={17} />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-leaf" />
        </button>
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="rounded-xl p-2 text-mist-400 transition-colors hover:bg-white/[0.05] hover:text-mist-50"
          >
            <MoreVertical size={17} />
          </button>
          {showMenu && (
            <div className="glass-panel animate-rise absolute right-0 z-[1500] mt-2 w-56 overflow-hidden rounded-2xl py-1">
              <MenuItem icon={<Info size={15} />} onClick={() => setShowMenu(false)}>О системе</MenuItem>
              <MenuItem icon={<FileText size={15} />} onClick={() => setShowMenu(false)}>Документация</MenuItem>
              <MenuItem icon={<MessageCircle size={15} />} onClick={() => setShowMenu(false)}>Обратная связь</MenuItem>
              <MenuItem icon={<AlertTriangle size={15} />} danger onClick={() => setShowMenu(false)}>Сообщить об ошибке</MenuItem>
            </div>
          )}
        </div>
        <div className="relative" ref={profileRef}>
          <button
            onClick={() => setShowProfile(!showProfile)}
            className="flex items-center gap-2 rounded-xl py-1 pl-1 pr-2 transition-colors hover:bg-white/[0.05]"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-leaf to-leaf-dim">
              <User size={14} className="text-leaf-ink" />
            </div>
            <div className="hidden text-left lg:block">
              <p className="text-xs font-semibold leading-none">Администратор</p>
              <p className="mt-1 text-[10px] text-mist-500">ООО «ЛандДизайн»</p>
            </div>
            <ChevronDown size={14} className="hidden text-mist-500 lg:block" />
          </button>
          {showProfile && (
            <div className="glass-panel animate-rise absolute right-0 z-[1500] mt-2 w-60 overflow-hidden rounded-2xl">
              <div className="border-b border-white/[0.06] px-4 py-3">
                <p className="text-sm font-semibold">admin@landesign.ru</p>
                <p className="mt-0.5 text-[11px] text-mist-500">Организация · полный доступ</p>
              </div>
              <div className="py-1">
                <MenuItem icon={<User size={15} />} onClick={() => setShowProfile(false)}>Аккаунт</MenuItem>
                <MenuItem icon={<LogOut size={15} />} danger onClick={() => setShowProfile(false)}>Выйти</MenuItem>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

function MenuItem({
  icon, children, onClick, danger,
}: { icon: ReactNode; children: ReactNode; onClick: () => void; danger?: boolean }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-[13px] transition-colors',
        danger ? 'text-accent-red hover:bg-accent-red/10' : 'text-mist-200 hover:bg-white/[0.05] hover:text-white',
      )}
    >
      {icon}
      {children}
    </button>
  )
}

export function TopBar({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="flex shrink-0 items-center justify-between px-5 pb-2">
      <p className="text-sm font-semibold text-mist-200">{title}</p>
      <div className="flex items-center gap-3">{children}</div>
    </div>
  )
}

export function FolderOpenIcon() {
  return <FolderOpen size={15} />
}
