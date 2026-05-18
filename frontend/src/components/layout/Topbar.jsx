import { Bell, LogOut, Menu, Search } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { eventsWs } from '../../lib/ws'

export default function Topbar({ title, onMenuClick }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    eventsWs.disconnect()
    logout()
    navigate('/login')
  }

  const initials = user?.full_name
    ?.split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || 'NF'

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-slate-800 bg-slate-950/90 px-4 backdrop-blur-md sm:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
          aria-label="Open menu"
        >
          <Menu size={22} />
        </button>
        {title && (
          <p className="text-sm font-medium text-slate-400 lg:hidden">{title}</p>
        )}
      </div>

      <div className="hidden flex-1 max-w-md lg:block">
        <div className="relative">
          <Search
            size={16}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
          />
          <input
            type="search"
            placeholder="Search devices, events..."
            className="w-full rounded-lg border border-slate-800 bg-slate-900/80 py-2 pl-9 pr-4 text-sm text-slate-200 placeholder:text-slate-500 focus:border-orange-500/50 focus:outline-none focus:ring-1 focus:ring-orange-500/30"
          />
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <button
          type="button"
          className="relative rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
          aria-label="Notifications"
        >
          <Bell size={20} />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500 ring-2 ring-slate-950" />
        </button>
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
          aria-label="Log out"
        >
          <LogOut size={20} />
        </button>
        <div className="hidden h-8 w-px bg-slate-800 sm:block" />
        <div className="flex items-center gap-2">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium text-slate-200">{user?.full_name}</p>
            <p className="text-xs capitalize text-slate-500">
              {user?.role?.replace('_', ' ')} · {user?.organization_name}
            </p>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-slate-700 to-slate-800 text-xs font-bold text-slate-300 ring-2 ring-slate-700">
            {initials}
          </div>
        </div>
      </div>
    </header>
  )
}
