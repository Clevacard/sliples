import { useEffect, useState } from 'react'
import { useSchedulesStore } from '../store/schedules'
import Modal, { ModalBody } from '../components/Modal'
import ScheduleForm from '../components/ScheduleForm'
import type { Schedule, ScheduleCreate, ScheduleUpdate } from '../api/client'

function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return 'Never'

  const date = new Date(dateString)
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffMins = Math.round(diffMs / (1000 * 60))
  const diffHours = Math.round(diffMs / (1000 * 60 * 60))
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24))

  if (diffMs < 0) {
    // Past
    const absDiffMins = Math.abs(diffMins)
    const absDiffHours = Math.abs(diffHours)
    const absDiffDays = Math.abs(diffDays)

    if (absDiffMins < 1) return 'Just now'
    if (absDiffMins < 60) return `${absDiffMins} min ago`
    if (absDiffHours < 24) return `${absDiffHours} hour${absDiffHours > 1 ? 's' : ''} ago`
    if (absDiffDays < 7) return `${absDiffDays} day${absDiffDays > 1 ? 's' : ''} ago`
    return date.toLocaleDateString()
  } else {
    // Future
    if (diffMins < 1) return 'Any moment'
    if (diffMins < 60) return `in ${diffMins} min`
    if (diffHours < 24) return `in ${diffHours} hour${diffHours > 1 ? 's' : ''}`
    if (diffDays < 7) return `in ${diffDays} day${diffDays > 1 ? 's' : ''}`
    return date.toLocaleDateString()
  }
}

function formatDateTime(dateString: string | null): string {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

export default function Schedules() {
  const {
    schedules,
    isLoading,
    error,
    fetchSchedules,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    toggleSchedule,
    runScheduleNow,
    clearError,
  } = useSchedulesStore()

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null)
  const [deletingSchedule, setDeletingSchedule] = useState<Schedule | null>(null)

  // Form submission states
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [runningScheduleId, setRunningScheduleId] = useState<string | null>(null)

  useEffect(() => {
    fetchSchedules()
  }, [fetchSchedules])

  const handleCreate = async (data: ScheduleCreate | ScheduleUpdate) => {
    setIsSubmitting(true)
    try {
      await createSchedule(data as ScheduleCreate)
      setShowCreateModal(false)
    } catch (err) {
      // Error is handled by the store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdate = async (data: ScheduleCreate | ScheduleUpdate) => {
    if (!editingSchedule) return
    setIsSubmitting(true)
    try {
      await updateSchedule(editingSchedule.id, data as ScheduleUpdate)
      setEditingSchedule(null)
    } catch (err) {
      // Error is handled by the store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!deletingSchedule) return
    setIsSubmitting(true)
    try {
      await deleteSchedule(deletingSchedule.id)
      setDeletingSchedule(null)
    } catch (err) {
      // Error is handled by the store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleToggle = async (schedule: Schedule) => {
    try {
      await toggleSchedule(schedule.id)
    } catch (err) {
      // Error is handled by the store
    }
  }

  const handleRunNow = async (schedule: Schedule) => {
    setRunningScheduleId(schedule.id)
    try {
      await runScheduleNow(schedule.id)
      // Optionally show a success toast
    } catch (err) {
      // Error is handled by the store
    } finally {
      setRunningScheduleId(null)
    }
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">Schedules</h1>
          <p className="text-gray-400 mt-1">
            Configure automated test runs on a schedule
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Schedule
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
      {isLoading && schedules.length === 0 ? (
        <div className="text-center py-12">
          <svg className="animate-spin h-8 w-8 mx-auto text-primary-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="mt-4 text-gray-400">Loading schedules...</p>
        </div>
      ) : schedules.length === 0 ? (
        /* Empty State */
        <div className="text-center py-12 bg-gray-800 rounded-xl border border-gray-700">
          <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-300 mb-2">No schedules configured</h3>
          <p className="text-gray-500 mb-6">
            Create a schedule to run your tests automatically.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
          >
            Create Your First Schedule
          </button>
        </div>
      ) : (
        /* Schedules Grid */
        <div className="grid gap-4">
          {schedules.map((schedule) => (
            <div
              key={schedule.id}
              className={`bg-gray-800 rounded-xl border overflow-hidden transition-all ${
                schedule.enabled ? 'border-gray-700' : 'border-gray-700/50 opacity-70'
              }`}
            >
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-gray-100 truncate">
                        {schedule.name}
                      </h3>
                      <span
                        className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                          schedule.enabled
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-gray-600 text-gray-400'
                        }`}
                      >
                        {schedule.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>

                    {/* Cron Description */}
                    <div className="flex items-center gap-2 mt-2 text-sm text-gray-300">
                      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>{schedule.cron_description}</span>
                      <span className="text-gray-500 font-mono text-xs">({schedule.cron_expression})</span>
                    </div>

                    {/* Details */}
                    <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-gray-400">
                      {/* Environment */}
                      <div className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
                        </svg>
                        <span>{schedule.environment_name || 'Unknown'}</span>
                      </div>

                      {/* Browsers */}
                      <div className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
                        </svg>
                        <span>{schedule.browsers.join(', ')}</span>
                      </div>

                      {/* Tags/Scenarios */}
                      {schedule.scenario_tags.length > 0 && (
                        <div className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                          </svg>
                          <span>{schedule.scenario_tags.map((t) => `@${t}`).join(', ')}</span>
                        </div>
                      )}
                      {schedule.scenario_ids.length > 0 && (
                        <div className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                          <span>{schedule.scenario_ids.length} scenario{schedule.scenario_ids.length > 1 ? 's' : ''}</span>
                        </div>
                      )}
                    </div>

                    {/* Run Info */}
                    <div className="flex items-center gap-6 mt-3 text-xs text-gray-500">
                      <div>
                        <span className="text-gray-400">Next run:</span>{' '}
                        <span className={schedule.enabled ? 'text-primary-400' : ''}>
                          {schedule.enabled ? formatRelativeTime(schedule.next_run_at) : 'Disabled'}
                        </span>
                        {schedule.next_run_at && schedule.enabled && (
                          <span className="ml-1 text-gray-600">({formatDateTime(schedule.next_run_at)})</span>
                        )}
                      </div>
                      <div>
                        <span className="text-gray-400">Last run:</span>{' '}
                        <span>{formatRelativeTime(schedule.last_run_at)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 ml-4">
                    {/* Toggle */}
                    <button
                      onClick={() => handleToggle(schedule)}
                      className={`relative w-10 h-5 rounded-full transition-colors ${
                        schedule.enabled ? 'bg-primary-600' : 'bg-gray-600'
                      }`}
                      title={schedule.enabled ? 'Disable' : 'Enable'}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                          schedule.enabled ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      />
                    </button>

                    {/* Run Now */}
                    <button
                      onClick={() => handleRunNow(schedule)}
                      disabled={runningScheduleId === schedule.id}
                      className="p-2 text-gray-400 hover:text-green-400 hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
                      title="Run now"
                    >
                      {runningScheduleId === schedule.id ? (
                        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                    </button>

                    {/* Edit */}
                    <button
                      onClick={() => setEditingSchedule(schedule)}
                      className="p-2 text-gray-400 hover:text-primary-400 hover:bg-gray-700 rounded-lg transition-colors"
                      title="Edit"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>

                    {/* Delete */}
                    <button
                      onClick={() => setDeletingSchedule(schedule)}
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
        title="Add Schedule"
        size="lg"
      >
        <ModalBody>
          <ScheduleForm
            onSubmit={handleCreate}
            onCancel={() => setShowCreateModal(false)}
            isLoading={isSubmitting}
          />
        </ModalBody>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingSchedule}
        onClose={() => setEditingSchedule(null)}
        title="Edit Schedule"
        size="lg"
      >
        <ModalBody>
          <ScheduleForm
            schedule={editingSchedule}
            onSubmit={handleUpdate}
            onCancel={() => setEditingSchedule(null)}
            isLoading={isSubmitting}
          />
        </ModalBody>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingSchedule}
        onClose={() => setDeletingSchedule(null)}
        title="Delete Schedule"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Are you sure you want to delete the schedule{' '}
            <span className="font-semibold text-gray-100">
              "{deletingSchedule?.name}"
            </span>
            ?
          </p>
          <p className="text-sm text-gray-500">
            This action cannot be undone. Scheduled runs will no longer execute automatically.
          </p>
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-700">
            <button
              onClick={() => setDeletingSchedule(null)}
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
              {isSubmitting ? 'Deleting...' : 'Delete Schedule'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
