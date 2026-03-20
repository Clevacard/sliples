import { useEffect, useState, useMemo } from 'react'
import { useCustomStepsStore } from '../store/customSteps'
import Modal, { ModalBody } from '../components/Modal'
import StepEditor from '../components/StepEditor'
import type { CustomStep, CustomStepCreate, CustomStepUpdate } from '../api/client'

export default function CustomSteps() {
  const {
    steps,
    isLoading,
    error,
    fetchSteps,
    createStep,
    updateStep,
    deleteStep,
    clearError,
  } = useCustomStepsStore()

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingStep, setEditingStep] = useState<CustomStep | null>(null)
  const [deletingStep, setDeletingStep] = useState<CustomStep | null>(null)

  // Filter state
  const [searchQuery, setSearchQuery] = useState('')

  // Form submission state
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    fetchSteps()
  }, [fetchSteps])

  // Filter steps
  const filteredSteps = useMemo(() => {
    if (!searchQuery.trim()) return steps

    const query = searchQuery.toLowerCase()
    return steps.filter((step) => {
      return (
        step.name.toLowerCase().includes(query) ||
        step.pattern.toLowerCase().includes(query) ||
        step.description?.toLowerCase().includes(query)
      )
    })
  }, [steps, searchQuery])

  const handleCreate = async (data: CustomStepCreate | CustomStepUpdate) => {
    setIsSubmitting(true)
    try {
      await createStep(data as CustomStepCreate)
      setShowCreateModal(false)
    } catch (err) {
      // Error handled by store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdate = async (data: CustomStepCreate | CustomStepUpdate) => {
    if (!editingStep) return
    setIsSubmitting(true)
    try {
      await updateStep(editingStep.id, data as CustomStepUpdate)
      setEditingStep(null)
    } catch (err) {
      // Error handled by store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!deletingStep) return
    setIsSubmitting(true)
    try {
      await deleteStep(deletingStep.id)
      setDeletingStep(null)
    } catch (err) {
      // Error handled by store
    } finally {
      setIsSubmitting(false)
    }
  }

  // Format date for display
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">Custom Steps</h1>
          <p className="text-gray-400 mt-1">
            Create reusable Gherkin step definitions with Python implementations
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Step
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
      {steps.length > 0 && (
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
              placeholder="Search by name or pattern..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-300"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
          {searchQuery && (
            <p className="mt-2 text-sm text-gray-500">
              Showing {filteredSteps.length} of {steps.length} steps
            </p>
          )}
        </div>
      )}

      {/* Loading State */}
      {isLoading && steps.length === 0 ? (
        <div className="text-center py-12">
          <svg className="animate-spin h-8 w-8 mx-auto text-primary-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="mt-4 text-gray-400">Loading custom steps...</p>
        </div>
      ) : steps.length === 0 ? (
        /* Empty State */
        <div className="text-center py-12 bg-gray-800 rounded-xl border border-gray-700">
          <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
          <h3 className="text-lg font-medium text-gray-300 mb-2">No custom steps yet</h3>
          <p className="text-gray-500 mb-6">
            Create custom step definitions to extend your test capabilities.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
          >
            Create Your First Step
          </button>
        </div>
      ) : filteredSteps.length === 0 ? (
        /* No search results */
        <div className="text-center py-12 bg-gray-800 rounded-xl border border-gray-700">
          <svg className="w-12 h-12 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <p className="text-gray-400 mb-2">No steps match your search</p>
          <button onClick={() => setSearchQuery('')} className="text-primary-400 hover:text-primary-300 text-sm">
            Clear search
          </button>
        </div>
      ) : (
        /* Steps List */
        <div className="space-y-4">
          {filteredSteps.map((step) => (
            <div
              key={step.id}
              className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden hover:border-gray-600 transition-colors"
            >
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    {/* Step Name */}
                    <h3 className="text-lg font-semibold text-gray-100 truncate">
                      {step.name}
                    </h3>

                    {/* Pattern */}
                    <div className="mt-2 font-mono text-sm bg-gray-900 rounded px-3 py-2 border border-gray-700">
                      <span className="text-purple-400">When </span>
                      <span className="text-gray-300">{step.pattern}</span>
                    </div>

                    {/* Description */}
                    {step.description && (
                      <p className="mt-2 text-sm text-gray-400">{step.description}</p>
                    )}

                    {/* Metadata */}
                    <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                      <span>Created: {formatDate(step.created_at)}</span>
                      {step.updated_at && step.updated_at !== step.created_at && (
                        <span>Updated: {formatDate(step.updated_at)}</span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => setEditingStep(step)}
                      className="p-2 text-gray-400 hover:text-primary-400 hover:bg-gray-700 rounded-lg transition-colors"
                      title="Edit"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => setDeletingStep(step)}
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
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Custom Step"
        size="full"
      >
        <ModalBody>
          <StepEditor
            onSave={handleCreate}
            onCancel={() => setShowCreateModal(false)}
            isLoading={isSubmitting}
          />
        </ModalBody>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingStep}
        onClose={() => setEditingStep(null)}
        title="Edit Custom Step"
        size="full"
      >
        <ModalBody>
          <StepEditor
            step={editingStep}
            onSave={handleUpdate}
            onCancel={() => setEditingStep(null)}
            isLoading={isSubmitting}
          />
        </ModalBody>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingStep}
        onClose={() => setDeletingStep(null)}
        title="Delete Custom Step"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Are you sure you want to delete the step{' '}
            <span className="font-semibold text-gray-100">"{deletingStep?.name}"</span>?
          </p>
          <div className="p-3 bg-gray-900 rounded-lg border border-gray-700 font-mono text-sm">
            <span className="text-purple-400">When </span>
            <span className="text-gray-300">{deletingStep?.pattern}</span>
          </div>
          <p className="text-sm text-gray-500">
            This action cannot be undone. Scenarios using this step definition may fail.
          </p>
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-700">
            <button
              onClick={() => setDeletingStep(null)}
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
              {isSubmitting ? 'Deleting...' : 'Delete Step'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
