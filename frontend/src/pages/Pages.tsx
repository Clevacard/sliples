import { useEffect, useState, useMemo } from 'react'
import { usePagesStore } from '../store/pages'
import { useEnvironmentsStore } from '../store/environments'
import Modal from '../components/Modal'
import type { Page, PageCreate, PageUpdate, PageOverrideCreate } from '../api/client'

export default function Pages() {
  const {
    pages,
    isLoading,
    error,
    fetchPages,
    createPage,
    updatePage,
    deletePage,
    addOverride,
    removeOverride,
    clearError,
  } = usePagesStore()

  const { environments, fetchEnvironments } = useEnvironmentsStore()

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingPage, setEditingPage] = useState<Page | null>(null)
  const [deletingPage, setDeletingPage] = useState<Page | null>(null)
  const [managingOverrides, setManagingOverrides] = useState<Page | null>(null)

  // Filter state
  const [searchQuery, setSearchQuery] = useState('')

  // Form state
  const [formData, setFormData] = useState<PageCreate>({ name: '', path: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Override form state
  const [overrideEnvId, setOverrideEnvId] = useState('')
  const [overridePath, setOverridePath] = useState('')

  useEffect(() => {
    fetchPages()
    fetchEnvironments()
  }, [fetchPages, fetchEnvironments])

  // Filter pages
  const filteredPages = useMemo(() => {
    if (!searchQuery.trim()) return pages

    const query = searchQuery.toLowerCase()
    return pages.filter((page) => {
      return (
        page.name.toLowerCase().includes(query) ||
        page.path.toLowerCase().includes(query) ||
        page.description?.toLowerCase().includes(query)
      )
    })
  }, [pages, searchQuery])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      await createPage(formData)
      setShowCreateModal(false)
      setFormData({ name: '', path: '' })
    } catch {
      // Error handled by store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingPage) return
    setIsSubmitting(true)
    try {
      await updatePage(editingPage.id, formData as PageUpdate)
      setEditingPage(null)
      setFormData({ name: '', path: '' })
    } catch {
      // Error handled by store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!deletingPage) return
    setIsSubmitting(true)
    try {
      await deletePage(deletingPage.id)
      setDeletingPage(null)
    } catch {
      // Error handled by store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleAddOverride = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!managingOverrides || !overrideEnvId) return
    setIsSubmitting(true)
    try {
      await addOverride(managingOverrides.id, {
        environment_id: overrideEnvId,
        path: overridePath,
      } as PageOverrideCreate)
      setOverrideEnvId('')
      setOverridePath('')
      // Refresh the page we're managing
      const updated = pages.find(p => p.id === managingOverrides.id)
      if (updated) setManagingOverrides(updated)
    } catch {
      // Error handled by store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRemoveOverride = async (overrideId: string) => {
    if (!managingOverrides) return
    try {
      await removeOverride(managingOverrides.id, overrideId)
      // Refresh the page we're managing
      const updated = pages.find(p => p.id === managingOverrides.id)
      if (updated) setManagingOverrides(updated)
    } catch {
      // Error handled by store
    }
  }

  const openEditModal = (page: Page) => {
    setFormData({
      name: page.name,
      path: page.path,
      description: page.description || undefined,
    })
    setEditingPage(page)
  }

  // Get environments that don't have overrides yet
  const availableEnvsForOverride = useMemo(() => {
    if (!managingOverrides) return []
    const usedEnvIds = new Set(managingOverrides.overrides.map(o => o.environment_id))
    return environments.filter(e => !usedEnvIds.has(e.id))
  }, [managingOverrides, environments])

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">Pages</h1>
          <p className="text-gray-400 mt-1">
            Define named pages with URL paths for use in test scenarios
          </p>
        </div>
        <button
          onClick={() => {
            setFormData({ name: '', path: '' })
            setShowCreateModal(true)
          }}
          className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Page
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg flex items-center justify-between">
          <p className="text-red-200">{error}</p>
          <button onClick={clearError} className="text-red-400 hover:text-red-200">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Search Filter */}
      {pages.length > 0 && (
        <div className="mb-6">
          <div className="relative max-w-md">
            <svg
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500"
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
            <input
              type="text"
              className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Search by name or path..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && pages.length === 0 ? (
        <div className="text-center py-12">
          <svg className="animate-spin h-8 w-8 mx-auto text-primary-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="mt-4 text-gray-400">Loading pages...</p>
        </div>
      ) : pages.length === 0 ? (
        /* Empty State */
        <div className="text-center py-12 bg-gray-800 rounded-xl border border-gray-700">
          <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-300 mb-2">No pages defined</h3>
          <p className="text-gray-500 mb-6 max-w-md mx-auto">
            Pages let you define named URLs like "Login" or "Dashboard" that can be used in Gherkin scenarios:
            <code className="block mt-2 text-sm bg-gray-900 px-3 py-2 rounded text-purple-400">
              When I navigate to the "Login" page
            </code>
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
          >
            Add Your First Page
          </button>
        </div>
      ) : (
        /* Pages Table */
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-900/50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Path
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Overrides
                </th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {filteredPages.map((page) => (
                <tr key={page.id} className="hover:bg-gray-700/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="text-gray-100 font-medium">{page.name}</div>
                    {page.description && (
                      <div className="text-sm text-gray-500 mt-1">{page.description}</div>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <code className="text-sm bg-gray-900 px-2 py-1 rounded text-blue-400">
                      {page.path}
                    </code>
                  </td>
                  <td className="px-6 py-4">
                    {page.overrides.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {page.overrides.map((o) => (
                          <span
                            key={o.id}
                            className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded"
                            title={`${o.environment_name}: ${o.path}`}
                          >
                            {o.environment_name}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-500 text-sm">None</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setManagingOverrides(page)}
                        className="p-2 text-gray-400 hover:text-yellow-400 hover:bg-gray-700 rounded-lg transition-colors"
                        title="Manage overrides"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => openEditModal(page)}
                        className="p-2 text-gray-400 hover:text-primary-400 hover:bg-gray-700 rounded-lg transition-colors"
                        title="Edit"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => setDeletingPage(page)}
                        className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg transition-colors"
                        title="Delete"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Add Page"
        size="md"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="e.g., Login, Dashboard, Product List"
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Used in Gherkin: When I navigate to the "{formData.name || 'Name'}" page
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Path</label>
            <input
              type="text"
              value={formData.path}
              onChange={(e) => setFormData({ ...formData, path: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="e.g., /login, /dashboard, /products"
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Appended to environment base URL
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Description (optional)</label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Brief description of this page"
              rows={2}
            />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-700">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'Add Page'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingPage}
        onClose={() => setEditingPage(null)}
        title="Edit Page"
        size="md"
      >
        <form onSubmit={handleUpdate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Path</label>
            <input
              type="text"
              value={formData.path}
              onChange={(e) => setFormData({ ...formData, path: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={2}
            />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-700">
            <button
              type="button"
              onClick={() => setEditingPage(null)}
              className="px-4 py-2 text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingPage}
        onClose={() => setDeletingPage(null)}
        title="Delete Page"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Are you sure you want to delete the page{' '}
            <span className="font-semibold text-gray-100">"{deletingPage?.name}"</span>?
          </p>
          <p className="text-sm text-gray-500">
            Scenarios using this page name may fail after deletion.
          </p>
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-700">
            <button
              onClick={() => setDeletingPage(null)}
              className="px-4 py-2 text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Deleting...' : 'Delete Page'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Manage Overrides Modal */}
      <Modal
        isOpen={!!managingOverrides}
        onClose={() => setManagingOverrides(null)}
        title={`Environment Overrides: ${managingOverrides?.name}`}
        size="lg"
      >
        <div className="space-y-6">
          {/* Current overrides */}
          <div>
            <h4 className="text-sm font-medium text-gray-300 mb-3">Current Overrides</h4>
            {managingOverrides?.overrides.length === 0 ? (
              <p className="text-gray-500 text-sm">No overrides configured. All environments use the default path.</p>
            ) : (
              <div className="space-y-2">
                {managingOverrides?.overrides.map((override) => (
                  <div
                    key={override.id}
                    className="flex items-center justify-between p-3 bg-gray-700 rounded-lg"
                  >
                    <div>
                      <span className="text-gray-100 font-medium">{override.environment_name}</span>
                      <code className="ml-3 text-sm text-blue-400">{override.path}</code>
                    </div>
                    <button
                      onClick={() => handleRemoveOverride(override.id)}
                      className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                      title="Remove override"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add new override */}
          {availableEnvsForOverride.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-3">Add Override</h4>
              <form onSubmit={handleAddOverride} className="flex gap-3">
                <select
                  value={overrideEnvId}
                  onChange={(e) => setOverrideEnvId(e.target.value)}
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option value="">Select environment...</option>
                  {availableEnvsForOverride.map((env) => (
                    <option key={env.id} value={env.id}>{env.name}</option>
                  ))}
                </select>
                <input
                  type="text"
                  value={overridePath}
                  onChange={(e) => setOverridePath(e.target.value)}
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Override path, e.g., /auth/login"
                  required
                />
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors disabled:opacity-50"
                  disabled={isSubmitting || !overrideEnvId}
                >
                  Add
                </button>
              </form>
            </div>
          )}

          {/* Info */}
          <div className="p-3 bg-gray-900 rounded-lg border border-gray-700">
            <p className="text-sm text-gray-400">
              <strong className="text-gray-300">Default path:</strong>{' '}
              <code className="text-blue-400">{managingOverrides?.path}</code>
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Overrides let you use different paths for specific environments when they don't follow the standard URL pattern.
            </p>
          </div>

          <div className="flex justify-end pt-4 border-t border-gray-700">
            <button
              onClick={() => setManagingOverrides(null)}
              className="px-4 py-2 text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
