import { useState, useRef, useEffect } from 'react'
import { UserInfo } from '../store/users'
import { useAuthStore } from '../store/auth'

interface UserListProps {
  users: UserInfo[]
  onChangeRole: (userId: string, role: 'admin' | 'user') => void
  onToggleActive: (userId: string, isActive: boolean) => void
}

function formatDate(dateString: string | null): string {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

interface ActionMenuProps {
  user: UserInfo
  isCurrentUser: boolean
  onChangeRole: (role: 'admin' | 'user') => void
  onToggleActive: (isActive: boolean) => void
}

function ActionMenu({ user, isCurrentUser, onChangeRole, onToggleActive }: ActionMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors"
        aria-label="Actions"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-lg border border-gray-700 py-1 z-10">
          {/* Role options */}
          <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Change Role
          </div>
          <button
            onClick={() => {
              onChangeRole('admin')
              setIsOpen(false)
            }}
            disabled={isCurrentUser && user.role === 'admin'}
            className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 ${
              user.role === 'admin'
                ? 'text-purple-400 bg-purple-500/10'
                : 'text-gray-300 hover:bg-gray-700'
            } ${isCurrentUser && user.role === 'admin' ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                user.role === 'admin' ? 'bg-purple-400' : 'bg-gray-600'
              }`}
            />
            Admin
            {user.role === 'admin' && (
              <svg className="w-4 h-4 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </button>
          <button
            onClick={() => {
              onChangeRole('user')
              setIsOpen(false)
            }}
            disabled={isCurrentUser}
            className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 ${
              user.role === 'user'
                ? 'text-blue-400 bg-blue-500/10'
                : 'text-gray-300 hover:bg-gray-700'
            } ${isCurrentUser ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                user.role === 'user' ? 'bg-blue-400' : 'bg-gray-600'
              }`}
            />
            User
            {user.role === 'user' && (
              <svg className="w-4 h-4 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </button>

          <div className="border-t border-gray-700 my-1" />

          {/* Active status */}
          <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Status
          </div>
          <button
            onClick={() => {
              onToggleActive(!user.is_active)
              setIsOpen(false)
            }}
            disabled={isCurrentUser}
            className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 ${
              isCurrentUser ? 'opacity-50 cursor-not-allowed text-gray-500' : 'text-gray-300 hover:bg-gray-700'
            }`}
          >
            {user.is_active ? (
              <>
                <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
                Deactivate User
              </>
            ) : (
              <>
                <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Activate User
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}

export default function UserList({ users, onChangeRole, onToggleActive }: UserListProps) {
  const { user: currentUser } = useAuthStore()

  if (users.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-12 text-center">
        <svg
          className="w-12 h-12 mx-auto text-gray-600 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
        <p className="text-gray-400">No users found</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-gray-900/50 text-left">
            <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              User
            </th>
            <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Role
            </th>
            <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Last Login
            </th>
            <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider text-right">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700">
          {users.map((user) => {
            const isCurrentUser = currentUser?.id === user.id

            return (
              <tr key={user.id} className="hover:bg-gray-700/30 transition-colors">
                {/* User info */}
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    {/* Avatar */}
                    {user.picture_url ? (
                      <img
                        src={user.picture_url}
                        alt={user.name}
                        className="w-10 h-10 rounded-full border border-gray-600"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center border border-gray-600">
                        <span className="text-sm font-medium text-gray-400">
                          {user.name?.charAt(0).toUpperCase() || '?'}
                        </span>
                      </div>
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-gray-100">{user.name}</p>
                        {isCurrentUser && (
                          <span className="text-xs text-gray-500">(you)</span>
                        )}
                      </div>
                      <p className="text-sm text-gray-400">{user.email}</p>
                    </div>
                  </div>
                </td>

                {/* Role badge */}
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                      user.role === 'admin'
                        ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                        : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    }`}
                  >
                    {user.role}
                  </span>
                </td>

                {/* Status badge */}
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                      user.is_active
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                        : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
                        user.is_active ? 'bg-green-400' : 'bg-gray-400'
                      }`}
                    />
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>

                {/* Last login */}
                <td className="px-6 py-4">
                  <p className="text-sm text-gray-400">{formatDate(user.last_login)}</p>
                </td>

                {/* Actions */}
                <td className="px-6 py-4 text-right">
                  <ActionMenu
                    user={user}
                    isCurrentUser={isCurrentUser}
                    onChangeRole={(role) => onChangeRole(user.id, role)}
                    onToggleActive={(isActive) => onToggleActive(user.id, isActive)}
                  />
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
