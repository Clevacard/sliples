import { Outlet, NavLink } from 'react-router-dom'
import UserMenu from './UserMenu'

const navigation = [
  { name: 'Dashboard', path: '/dashboard' },
  { name: 'Scenarios', path: '/scenarios' },
  { name: 'Custom Steps', path: '/custom-steps' },
  { name: 'Test Runs', path: '/runs' },
  { name: 'Environments', path: '/environments' },
  { name: 'Repos', path: '/repos' },
  { name: 'Settings', path: '/settings' },
]

export default function Layout() {
  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white">
        <div className="p-4">
          <h1 className="text-2xl font-bold text-primary-400">Sliples</h1>
          <p className="text-sm text-gray-400 mt-1">UI Automation Testing</p>
        </div>

        <nav className="mt-6">
          {navigation.map((item) => (
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
              {item.name}
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
