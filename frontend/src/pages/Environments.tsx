import { useEffect, useState } from 'react'
import { useEnvironmentsStore } from '../store/environments'
import Modal, { ModalBody } from '../components/Modal'
import EnvironmentForm from '../components/EnvironmentForm'
import type { Environment, EnvironmentCreate, EnvironmentUpdate } from '../api/client'

// Sensitive key patterns for masking display
const SENSITIVE_PATTERNS = [
  /password/i,
  /secret/i,
  /token/i,
  /api.?key/i,
  /credential/i,
  /auth/i,
]

function isSensitiveKey(key: string): boolean {
  return SENSITIVE_PATTERNS.some((pattern) => pattern.test(key))
}

function maskValue(value: string): string {
  if (value.length <= 4) {
    return '*'.repeat(value.length)
  }
  return value.substring(0, 2) + '*'.repeat(Math.min(value.length - 4, 8)) + value.substring(value.length - 2)
}

export default function Environments() {
  const {
    environments,
    isLoading,
    error,
    fetchEnvironments,
    createEnvironment,
    updateEnvironment,
    deleteEnvironment,
    clearError,
  } = useEnvironmentsStore()

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingEnvironment, setEditingEnvironment] = useState<Environment | null>(null)
  const [deletingEnvironment, setDeletingEnvironment] = useState<Environment | null>(null)

  // Expanded cards state
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set())

  // Form submission states
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    fetchEnvironments()
  }, [fetchEnvironments])

  const toggleCardExpand = (id: string) => {
    setExpandedCards((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const handleCreate = async (data: EnvironmentCreate | EnvironmentUpdate) => {
    setIsSubmitting(true)
    try {
      await createEnvironment(data as EnvironmentCreate)
      setShowCreateModal(false)
    } catch (err) {
      // Error is handled by the store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdate = async (data: EnvironmentCreate | EnvironmentUpdate) => {
    if (!editingEnvironment) return
    setIsSubmitting(true)
    try {
      await updateEnvironment(editingEnvironment.id, data as EnvironmentUpdate)
      setEditingEnvironment(null)
    } catch (err) {
      // Error is handled by the store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!deletingEnvironment) return
    setIsSubmitting(true)
    try {
      await deleteEnvironment(deletingEnvironment.id)
      setDeletingEnvironment(null)
    } catch (err) {
      // Error is handled by the store
    } finally {
      setIsSubmitting(false)
    }
  }

  const getVariableCount = (env: Environment): number => {
    return Object.keys(env.variables || {}).length
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">Environments</h1>
          <p className="text-gray-400 mt-1">
            Configure test environments with URLs and variables
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Environment
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg flex items-center justify-between">
          <p className="text-red-200">{error}</p>
          <button
            onClick={clearError}
            className="text-red-400 hover:text-red-200"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Loading State */}
      {isLoading && environments.length === 0 ? (
        <div className="text-center py-12">
          <svg className="animate-spin h-8 w-8 mx-auto text-primary-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="mt-4 text-gray-400">Loading environments...</p>
        </div>
      ) : environments.length === 0 ? (
        /* Empty State */
        <div className="text-center py-12 bg-gray-800 rounded-xl border border-gray-700">
          <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
          <h3 className="text-lg font-medium text-gray-300 mb-2">No environments configured</h3>
          <p className="text-gray-500 mb-6">
            Add an environment to start running tests against your applications.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
          >
            Create Your First Environment
          </button>
        </div>
      ) : (
        /* Environments Grid */
        <div className="grid gap-4">
          {environments.map((env) => {
            const isExpanded = expandedCards.has(env.id)
            const variableCount = getVariableCount(env)
            const variables = Object.entries(env.variables || {})

            return (
              <div
                key={env.id}
                className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden transition-all"
              >
                {/* Card Header */}
                <div className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <h3 className="text-lg font-semibold text-gray-100 truncate">
                          {env.name}
                        </h3>
                        <span className="px-2 py-0.5 text-xs font-medium bg-gray-700 text-gray-300 rounded-full">
                          {variableCount} variable{variableCount !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <p className="text-sm text-gray-400 mt-1 truncate">
                        {env.base_url}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Locale: {env.locale || 'en-GB'} · Timezone: {env.timezone_id || 'Europe/London'} · Retention: {env.retention_days} days
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 ml-4">
                      {variableCount > 0 && (
                        <button
                          onClick={() => toggleCardExpand(env.id)}
                          className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors"
                          title={isExpanded ? 'Collapse' : 'Expand'}
                        >
                          <svg
                            className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                      )}
                      <button
                        onClick={() => setEditingEnvironment(env)}
                        className="p-2 text-gray-400 hover:text-primary-400 hover:bg-gray-700 rounded-lg transition-colors"
                        title="Edit"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => setDeletingEnvironment(env)}
                        className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg transition-colors"
                        title="Delete"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Variables Section (Expandable) */}
                {isExpanded && variables.length > 0 && (
                  <div className="px-4 pb-4">
                    <div className="bg-gray-900 rounded-lg p-3 border border-gray-700">
                      <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
                        Variables
                      </h4>
                      <div className="space-y-1">
                        {variables.map(([key, value]) => {
                          const sensitive = isSensitiveKey(key)
                          return (
                            <div key={key} className="flex items-center text-sm font-mono">
                              <span className="text-primary-400">{key}</span>
                              <span className="text-gray-500 mx-2">=</span>
                              <span className="text-gray-300">
                                {sensitive ? maskValue(value) : value}
                              </span>
                              {sensitive && (
                                <span className="ml-2 text-xs text-yellow-500" title="Sensitive value">
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                  </svg>
                                </span>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Add Environment"
        size="lg"
      >
        <ModalBody>
          <EnvironmentForm
            onSubmit={handleCreate}
            onCancel={() => setShowCreateModal(false)}
            isLoading={isSubmitting}
          />
        </ModalBody>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingEnvironment}
        onClose={() => setEditingEnvironment(null)}
        title="Edit Environment"
        size="lg"
      >
        <ModalBody>
          <EnvironmentForm
            environment={editingEnvironment}
            onSubmit={handleUpdate}
            onCancel={() => setEditingEnvironment(null)}
            isLoading={isSubmitting}
          />
        </ModalBody>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingEnvironment}
        onClose={() => setDeletingEnvironment(null)}
        title="Delete Environment"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Are you sure you want to delete the environment{' '}
            <span className="font-semibold text-gray-100">
              "{deletingEnvironment?.name}"
            </span>
            ?
          </p>
          <p className="text-sm text-gray-500">
            This action cannot be undone. All test results associated with this environment
            will be preserved but will no longer be linked to an environment.
          </p>
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-700">
            <button
              onClick={() => setDeletingEnvironment(null)}
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
              {isSubmitting ? 'Deleting...' : 'Delete Environment'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
