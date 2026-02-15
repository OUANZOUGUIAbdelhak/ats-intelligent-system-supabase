import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, FileText, Search, Rocket } from 'lucide-react'
import { cn } from '@/lib/utils'

const nav = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/cvs', label: 'CVs', icon: FileText },
  { path: '/matching', label: 'Matching', icon: Search },
  { path: '/demo', label: 'Demo', icon: Rocket },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const loc = useLocation()
  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-slate-900 text-slate-200 border-r border-slate-800 flex flex-col">
        <div className="p-6 border-b border-slate-800">
          <h1 className="text-xl font-bold text-white">ATS</h1>
          <p className="text-sm text-slate-400">Intelligent System</p>
        </div>
        <nav className="p-4 space-y-1">
          {nav.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                loc.pathname === path
                  ? 'bg-primary-600 text-white'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              )}
            >
              <Icon className="w-5 h-5" />
              {label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-auto p-8">{children}</main>
    </div>
  )
}
