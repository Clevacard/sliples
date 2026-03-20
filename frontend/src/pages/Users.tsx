import { useEffect, useState } from 'react'
import { useUsersStore } from '../store/users'
import UserList from '../components/UserList'
import Modal, { ModalFooter } from '../components/Modal'

export default function Users() {
  const { users, isLoading, error, fetchUsers, updateRole, toggleActive, clearError } = useUsersStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  // Confirmation modal state
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean
    type: 'role' | 'active'
    userId: string
    userName: string
    newValue: string | boolean
  }>({
    isOpen: false,
    type: 'role',
    userId: '',
    userName: '',
    newValue: '',
  })
  const [isProcessing, setIsProcessing] = useState(false)

  // Toast notification state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchTerm])

  // Fetch users on mount and when search changes
  useEffect(() => {
    fetchUsers(debouncedSearch || undefined)
  }, [fetchUsers, debouncedSearch])

  // Show toast
  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  // Handle role change request
  const handleRoleChange = (userId: string, role: 'admin' | 'user') => {
    const user = users.find((u) => u.id === userId)
    if (!user || user.role === role) return

    setConfirmModal({
      isOpen: true,
      type: 'role',
      userId,
      userName: user.name,
      newValue: role,
    })
  }

  // Handle active toggle request
  const handleActiveToggle = (userId: string, isActive: boolean) => {
    const user = users.find((u) => u.id === userId)
    if (!user || user.is_active === isActive) return

    setConfirmModal({
      isOpen: true,
      type: 'active',
      userId,
      userName: user.name,
      newValue: isActive,
    })
  }

  // Confirm action
  const handleConfirm = async () => {
    setIsProcessing(true)
    try {
      if (confirmModal.type === 'role') {
        await updateRole(confirmModal.userId, confirmModal.newValue as 'admin' | 'user')
        showToast(`Role updated to ${confirmModal.newValue}`, 'success')
      } else {
        await toggleActive(confirmModal.userId, confirmModal.newValue as boolean)
        showToast(
          confirmModal.newValue ? 'User activated' : 'User deactivated',
          'success'
        )
      }
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Action failed', 'error')
    } finally {
      setIsProcessing(false)
      setConfirmModal({ ...confirmModal, isOpen: false })
    }
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-100">User Management</h1>
        <p className="text-gray-400 mt-2">
          Manage user accounts, roles, and access permissions.
        </p>
      </div>

      {/* Search bar */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg
              className="w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search by name or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-200"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg
              className="w-5 h-5 text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="text-red-400">{error}</span>
          </div>
          <button
            onClick={clearError}
            className="text-red-400 hover:text-red-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      )}

      {/* Loading state */}
      {isLoading ? (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-12 text-center">
          <div className="w-12 h-12 mx-auto mb-4">
            <svg
              className="animate-spin w-full h-full text-primary-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
          <p className="text-gray-400">Loading users...</p>
        </div>
      ) : (
        <UserList
          users={users}
          onChangeRole={handleRoleChange}
          onToggleActive={handleActiveToggle}
        />
      )}

      {/* Stats */}
      {!isLoading && users.length > 0 && (
        <div className="mt-6 flex items-center gap-6 text-sm text-gray-500">
          <span>{users.length} user{users.length !== 1 ? 's' : ''} total</span>
          <span>{users.filter((u) => u.role === 'admin').length} admin{users.filter((u) => u.role === 'admin').length !== 1 ? 's' : ''}</span>
          <span>{users.filter((u) => u.is_active).length} active</span>
        </div>
      )}

      {/* Confirmation Modal */}
      <Modal
        isOpen={confirmModal.isOpen}
        onClose={() => !isProcessing && setConfirmModal({ ...confirmModal, isOpen: false })}
        title={confirmModal.type === 'role' ? 'Change User Role' : 'Change User Status'}
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            {confirmModal.type === 'role' ? (
              <>
                Are you sure you want to change <span className="font-semibold text-gray-100">{confirmModal.userName}</span>'s role to{' '}
                <span
                  className={`font-semibold ${
                    confirmModal.newValue === 'admin' ? 'text-purple-400' : 'text-blue-400'
                  }`}
                >
                  {confirmModal.newValue as string}
                </span>
                ?
              </>
            ) : (
              <>
                Are you sure you want to{' '}
                <span className={`font-semibold ${confirmModal.newValue ? 'text-green-400' : 'text-red-400'}`}>
                  {confirmModal.newValue ? 'activate' : 'deactivate'}
                </span>{' '}
                <span className="font-semibold text-gray-100">{confirmModal.userName}</span>?
              </>
            )}
          </p>

          {confirmModal.type === 'role' && confirmModal.newValue === 'admin' && (
            <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <p className="text-sm text-yellow-400">
                Admin users have full access to all features including user management.
              </p>
            </div>
          )}

          {confirmModal.type === 'active' && !confirmModal.newValue && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
              <p className="text-sm text-red-400">
                Deactivated users will not be able to log in or access the system.
              </p>
            </div>
          )}

          <ModalFooter>
            <button
              onClick={() => setConfirmModal({ ...confirmModal, isOpen: false })}
              disabled={isProcessing}
              className="px-4 py-2 text-gray-300 hover:text-gray-100 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={isProcessing}
              className={`px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 ${
                confirmModal.type === 'active' && !confirmModal.newValue
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-primary-600 hover:bg-primary-700 text-white'
              }`}
            >
              {isProcessing ? (
                <span className="flex items-center gap-2">
                  <svg
                    className="animate-spin w-4 h-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Processing...
                </span>
              ) : (
                'Confirm'
              )}
            </button>
          </ModalFooter>
        </div>
      </Modal>

      {/* Toast notification */}
      {toast && (
        <div
          className={`fixed bottom-6 right-6 px-4 py-3 rounded-lg shadow-lg border flex items-center gap-3 animate-in slide-in-from-bottom-4 ${
            toast.type === 'success'
              ? 'bg-green-500/20 border-green-500/30 text-green-400'
              : 'bg-red-500/20 border-red-500/30 text-red-400'
          }`}
        >
          {toast.type === 'success' ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          )}
          {toast.message}
        </div>
      )}
    </div>
  )
}
