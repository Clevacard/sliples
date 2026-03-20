import { Outlet, NavLink } from 'react-router-dom'
import UserMenu from './UserMenu'
import { useAuthStore } from '../store/auth'

interface NavItem {
  name: string
  path: string
  adminOnly?: boolean
}

const navigation: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard' },
  { name: 'Scenarios', path: '/scenarios' },
  { name: 'Custom Steps', path: '/custom-steps' },
  { name: 'Test Runs', path: '/runs' },
  { name: 'Schedules', path: '/schedules' },
  { name: 'Environments', path: '/environments' },
  { name: 'Repos', path: '/repos' },
  { name: 'Settings', path: '/settings' },
  { name: 'Users', path: '/users', adminOnly: true },
]

export default function Layout() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin'

  // Filter navigation items based on user role
  const visibleNavigation = navigation.filter(
    (item) => !item.adminOnly || isAdmin
  )

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white">
        <div className="p-4">
          <h1 className="text-2xl font-bold text-primary-400">Sliples</h1>
          <p className="text-sm text-gray-400 mt-1">UI Automation Testing</p>
        </div>

        <nav className="mt-6">
          {visibleNavigation.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `block px-4 py-3 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-gray-800 text-white border-l-4 border-primary-500'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <span className="flex items-center gap-2">
                {item.name}
                {item.adminOnly && (
                  <span className="text-xs bg-purple-500/20 text-purple-400 px-1.5 py-0.5 rounded">
                    Admin
                  </span>
                )}
              </span>
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 w-64 p-4 text-xs text-gray-500">
          v0.1.0
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header with user menu */}
        <header className="h-14 bg-gray-800 border-b border-gray-700 flex items-center justify-end px-6">
          <UserMenu />
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
