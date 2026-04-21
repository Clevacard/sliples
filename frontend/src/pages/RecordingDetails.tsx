import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useRecordingsStore } from '../store/recordings'
import EditEventModal from '../components/EditEventModal'
import {
  RecordedEvent,
  PlaybackRun,
  startPlayback,
  getPlaybackRuns,
  getEnvironments,
  Environment,
} from '../api/client'
import { usePlaybackWebSocket, PlaybackStepResult } from '../hooks'

export default function RecordingDetails() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { currentSession, events, isLoading, error, fetchSessionDetails } = useRecordingsStore()
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null)
  const [editingEvent, setEditingEvent] = useState<RecordedEvent | null>(null)

  // Playback state
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [playbackRuns, setPlaybackRuns] = useState<PlaybackRun[]>([])
  const [showPlaybackModal, setShowPlaybackModal] = useState(false)
  const [selectedEnvId, setSelectedEnvId] = useState<string>('')
  const [selectedBrowser, setSelectedBrowser] = useState<string>('chrome')
  const [startingPlayback, setStartingPlayback] = useState(false)
  const [playbackError, setPlaybackError] = useState<string | null>(null)

  // Live playback tracking
  const [activePlaybackId, setActivePlaybackId] = useState<string | null>(null)
  const [liveStepResults, setLiveStepResults] = useState<PlaybackStepResult[]>([])

  // WebSocket hook for live updates
  const {
    connectionState,
    progressMessage: liveProgress,
    totalSteps: liveTotalSteps,
    currentStep: liveCurrentStep,
    passed: livePassed,
    failed: liveFailed,
    isComplete: liveIsComplete,
  } = usePlaybackWebSocket(activePlaybackId, {
    onStepResult: (result) => {
      setLiveStepResults((prev) => [...prev, result])
    },
    onComplete: () => {
      // Refresh playback runs when complete
      if (id) {
        getPlaybackRuns(id).then(setPlaybackRuns)
      }
      // Clear active playback after a delay
      setTimeout(() => {
        setActivePlaybackId(null)
        setLiveStepResults([])
      }, 3000)
    },
  })

  useEffect(() => {
    if (id) {
      fetchSessionDetails(id)
      loadPlaybackData(id)
    }
  }, [id, fetchSessionDetails])

  const loadPlaybackData = async (sessionId: string) => {
    try {
      const [envs, runs] = await Promise.all([getEnvironments(), getPlaybackRuns(sessionId)])
      setEnvironments(envs)
      setPlaybackRuns(runs)
      if (envs.length > 0 && !selectedEnvId) {
        setSelectedEnvId(envs[0].id)
        // Set default browser from first environment's config
        if (envs[0].browser_configs?.length > 0) {
          setSelectedBrowser(envs[0].browser_configs[0].browser)
        }
      }
    } catch (e) {
      console.error('Failed to load playback data:', e)
    }
  }

  // Get available browsers for selected environment
  const selectedEnv = environments.find((e) => e.id === selectedEnvId)
  const availableBrowsers = selectedEnv?.browser_configs || []

  // Update browser when environment changes
  const handleEnvChange = (envId: string) => {
    setSelectedEnvId(envId)
    const env = environments.find((e) => e.id === envId)
    if (env && env.browser_configs && env.browser_configs.length > 0) {
      setSelectedBrowser(env.browser_configs[0].browser)
    }
  }

  const handleStartPlayback = async () => {
    if (!id || !selectedEnvId) return
    setStartingPlayback(true)
    setPlaybackError(null)
    setLiveStepResults([])
    try {
      const run = await startPlayback(id, {
        environment_id: selectedEnvId,
        browser: selectedBrowser,
        viewport_width: currentSession?.viewport_width || undefined,
        viewport_height: currentSession?.viewport_height || undefined,
      })
      setPlaybackRuns([run, ...playbackRuns])
      setActivePlaybackId(run.id) // Start WebSocket connection
      setShowPlaybackModal(false)
    } catch (e: any) {
      setPlaybackError(e.message || 'Failed to start playback')
    } finally {
      setStartingPlayback(false)
    }
  }

  const refreshPlaybackRuns = async () => {
    if (id) {
      const runs = await getPlaybackRuns(id)
      setPlaybackRuns(runs)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-700 rounded w-40 animate-pulse" />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-700 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (!currentSession) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-400">Recording not found</p>
      </div>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const getDuration = () => {
    if (!currentSession.stopped_at) return 'Recording...'
    const start = new Date(currentSession.created_at)
    const end = new Date(currentSession.stopped_at)
    const seconds = Math.round((end.getTime() - start.getTime()) / 1000)
    return `${seconds}s`
  }

  const getEventTypeBadgeClass = (type: string) => {
    switch (type) {
      case 'click':
        return 'badge-info'
      case 'input':
      case 'change':
        return 'badge-warning'
      case 'submit':
        return 'badge-success'
      case 'navigation':
        return 'badge-primary'
      case 'keydown':
        return 'badge'
      default:
        return 'badge'
    }
  }

  const getElementDisplay = (event: RecordedEvent) => {
    if (event.step_label) return event.step_label
    if (event.label_text) return event.label_text
    if (event.element_id) return `#${event.element_id}`
    if (event.selector_test_id) return `[data-testid="${event.selector_test_id}"]`
    if (event.tag_name) return `<${event.tag_name}>`
    return 'Unknown element'
  }

  const getPlaybackStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-600 text-gray-200'
      case 'running':
        return 'bg-blue-600 text-blue-100'
      case 'passed':
        return 'bg-green-600 text-green-100'
      case 'failed':
        return 'bg-red-600 text-red-100'
      default:
        return 'bg-gray-600'
    }
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate('/recordings')}
        className="text-blue-400 hover:text-blue-300 flex items-center gap-2"
      >
        ← Back to Recordings
      </button>

      {/* Header */}
      <div className="card">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-1">{currentSession.name}</h1>
            <p className="text-gray-400 text-sm truncate">{currentSession.url}</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowPlaybackModal(true)}
              className="btn btn-primary"
              disabled={currentSession.status === 'recording'}
            >
              ▶ Run Playback
            </button>
            <span
              className={`badge ${currentSession.status === 'stopped' ? 'badge-success' : 'badge-info'}`}
            >
              {currentSession.status}
            </span>
          </div>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded p-3 mb-4">
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-gray-700/30 rounded p-3">
            <p className="text-xs text-gray-400 mb-1">Total Events</p>
            <p className="text-2xl font-bold text-white">{currentSession.event_count}</p>
          </div>
          <div className="bg-gray-700/30 rounded p-3">
            <p className="text-xs text-gray-400 mb-1">Screenshots</p>
            <p className="text-2xl font-bold text-white">
              {events.filter((e) => e.should_screenshot).length}
            </p>
          </div>
          <div className="bg-gray-700/30 rounded p-3">
            <p className="text-xs text-gray-400 mb-1">Duration</p>
            <p className="text-2xl font-bold text-white">{getDuration()}</p>
          </div>
          <div className="bg-gray-700/30 rounded p-3">
            <p className="text-xs text-gray-400 mb-1">Viewport</p>
            <p className="text-sm font-bold text-white">
              {currentSession.viewport_width}×{currentSession.viewport_height}
            </p>
          </div>
        </div>
      </div>

      {/* Live Playback Progress */}
      {activePlaybackId && (
        <div className="card border-2 border-blue-500/50 bg-blue-900/10">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
            <h2 className="text-xl font-semibold text-white">Live Playback</h2>
            <span className="text-sm text-gray-400">
              {connectionState === 'connected' ? 'Connected' : connectionState}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-400 mb-2">
              <span>{liveProgress || 'Starting...'}</span>
              <span>
                {liveCurrentStep} / {liveTotalSteps} steps
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-300 ${
                  liveIsComplete
                    ? liveFailed > 0
                      ? 'bg-red-500'
                      : 'bg-green-500'
                    : 'bg-blue-500'
                }`}
                style={{
                  width: `${liveTotalSteps > 0 ? (liveCurrentStep / liveTotalSteps) * 100 : 0}%`,
                }}
              />
            </div>
          </div>

          {/* Stats */}
          <div className="flex gap-6 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-green-400 font-bold text-xl">{livePassed}</span>
              <span className="text-gray-400 text-sm">passed</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-red-400 font-bold text-xl">{liveFailed}</span>
              <span className="text-gray-400 text-sm">failed</span>
            </div>
          </div>

          {/* Live Step Results */}
          {liveStepResults.length > 0 && (
            <div className="max-h-48 overflow-y-auto space-y-1 text-sm">
              {liveStepResults.map((step, i) => (
                <div
                  key={i}
                  className={`flex items-center gap-2 px-2 py-1 rounded ${
                    step.status === 'passed' ? 'bg-green-900/20' : 'bg-red-900/20'
                  }`}
                >
                  <span
                    className={`w-5 h-5 flex items-center justify-center rounded text-xs ${
                      step.status === 'passed'
                        ? 'bg-green-600 text-white'
                        : 'bg-red-600 text-white'
                    }`}
                  >
                    {step.step_number}
                  </span>
                  <span className="text-gray-400">{step.event_type}</span>
                  <span className="text-gray-200 truncate flex-1">{step.element}</span>
                  {step.error_message && (
                    <span className="text-red-400 text-xs truncate max-w-[200px]">
                      {step.error_message}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {liveIsComplete && (
            <div
              className={`mt-4 p-3 rounded text-center ${
                liveFailed > 0 ? 'bg-red-900/30 text-red-200' : 'bg-green-900/30 text-green-200'
              }`}
            >
              Playback {liveFailed > 0 ? 'failed' : 'passed'}! {livePassed} passed, {liveFailed}{' '}
              failed
            </div>
          )}
        </div>
      )}

      {/* Playback Runs */}
      {playbackRuns.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Playback Runs</h2>
            <button onClick={refreshPlaybackRuns} className="btn btn-sm btn-secondary">
              Refresh
            </button>
          </div>
          <table className="w-full table-dark">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left px-4 py-2 text-gray-300">Status</th>
                <th className="text-left px-4 py-2 text-gray-300">Browser</th>
                <th className="text-left px-4 py-2 text-gray-300">Steps</th>
                <th className="text-left px-4 py-2 text-gray-300">Duration</th>
                <th className="text-left px-4 py-2 text-gray-300">Started</th>
                <th className="text-right px-4 py-2 text-gray-300">Actions</th>
              </tr>
            </thead>
            <tbody>
              {playbackRuns.map((run) => (
                <tr key={run.id} className="border-b border-gray-700 hover:bg-gray-700/30">
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getPlaybackStatusBadge(run.status)}`}>
                      {run.status}
                    </span>
                    {run.progress_message && run.status === 'running' && (
                      <span className="ml-2 text-xs text-gray-400">{run.progress_message}</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-200">{run.browser}</td>
                  <td className="px-4 py-3 text-gray-200">
                    <span className="text-green-400">{run.passed_steps}</span>
                    {' / '}
                    <span className="text-red-400">{run.failed_steps}</span>
                    {' / '}
                    {run.total_steps}
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {run.duration_ms ? `${(run.duration_ms / 1000).toFixed(1)}s` : '-'}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-sm">
                    {run.started_at ? formatDate(run.started_at) : '-'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {(run.status === 'passed' || run.status === 'failed') && (
                      <a
                        href={`/api/v1/recorder/playback/${run.id}/report`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-sm bg-purple-600 hover:bg-purple-700 text-white"
                      >
                        View Report
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Events List */}
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4">Recorded Events</h2>
        {events.length > 0 ? (
          <div className="space-y-3">
            {events.map((event) => (
              <div key={event.id} className="bg-gray-700/20 rounded-lg">
                <button
                  onClick={() => setExpandedEventId(expandedEventId === event.id ? null : event.id)}
                  className="w-full text-left flex items-center justify-between hover:bg-gray-700/30 p-4 rounded-lg"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="w-8 h-8 bg-gray-700 rounded flex items-center justify-center text-xs text-gray-300 font-semibold">
                      {event.sequence}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className={`badge ${getEventTypeBadgeClass(event.event_type)}`}>
                          {event.event_type}
                        </span>
                        <span className="text-gray-200 font-medium">{getElementDisplay(event)}</span>
                        {event.should_screenshot && (
                          <span className="text-xs bg-blue-900/30 text-blue-300 px-2 py-1 rounded">
                            Screenshot
                          </span>
                        )}
                        {event.parameters && Object.keys(event.parameters).length > 0 && (
                          <span className="text-xs bg-green-900/30 text-green-300 px-2 py-1 rounded">
                            {Object.keys(event.parameters).length} param(s)
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-500 mt-2">
                        <span>{formatDate(event.timestamp)}</span>
                        {event.value && <span>Value: {event.value.substring(0, 50)}</span>}
                        {event.selector_test_id && <span>ID: {event.selector_test_id}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="text-gray-400">{expandedEventId === event.id ? '▼' : '▶'}</div>
                </button>

                {/* Expanded Details */}
                {expandedEventId === event.id && (
                  <div className="border-t border-gray-700 mx-4 mb-4 pt-4 space-y-4">
                    {/* Event Type & Value */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">Event Details</h4>
                      <div className="space-y-2 text-sm">
                        <div>
                          <span className="text-gray-500">Type:</span>
                          <span className="text-gray-200 ml-2">{event.event_type}</span>
                        </div>
                        {event.value && (
                          <div>
                            <span className="text-gray-500">Value:</span>
                            <span className="text-gray-200 ml-2 font-mono">{event.value}</span>
                          </div>
                        )}
                        {event.coordinates && (
                          <div>
                            <span className="text-gray-500">Coordinates:</span>
                            <span className="text-gray-200 ml-2">
                              x: {event.coordinates.x}, y: {event.coordinates.y}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Element Info */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">Element</h4>
                      <div className="space-y-2 text-sm">
                        {event.selector_css && (
                          <div>
                            <span className="text-gray-500">CSS:</span>
                            <span className="text-gray-200 ml-2 font-mono text-xs break-all">
                              {event.selector_css}
                            </span>
                          </div>
                        )}
                        {event.selector_test_id && (
                          <div>
                            <span className="text-gray-500">Test ID:</span>
                            <span className="text-gray-200 ml-2 font-mono">{event.selector_test_id}</span>
                          </div>
                        )}
                        {event.label_text && (
                          <div>
                            <span className="text-gray-500">Label:</span>
                            <span className="text-gray-200 ml-2">{event.label_text}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* User Annotations */}
                    <div className="bg-gray-700/20 rounded p-3">
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">Annotations</h4>
                      <div className="space-y-2 text-sm">
                        {event.step_label && (
                          <div>
                            <span className="text-gray-500">Step Label:</span>
                            <span className="text-blue-300 ml-2">{event.step_label}</span>
                          </div>
                        )}
                        {event.should_screenshot && (
                          <div className="text-green-300">✓ Mark for screenshot</div>
                        )}
                        {event.parameters && Object.keys(event.parameters).length > 0 && (
                          <div>
                            <span className="text-gray-500">Parameters:</span>
                            <div className="mt-1 space-y-1 ml-4">
                              {Object.entries(event.parameters).map(([key, value]) => (
                                <div key={key} className="font-mono text-xs text-green-300">
                                  {key} = ${'{'}
                                  {value}
                                  {'}'}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        {event.notes && (
                          <div>
                            <span className="text-gray-500">Notes:</span>
                            <p className="text-gray-200 ml-2 mt-1 text-xs">{event.notes}</p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Edit Button */}
                    <button
                      onClick={() => setEditingEvent(event)}
                      className="w-full btn btn-sm bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      Edit Annotations
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-400">No events recorded</p>
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editingEvent && <EditEventModal event={editingEvent} onClose={() => setEditingEvent(null)} />}

      {/* Playback Modal */}
      {showPlaybackModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">Start Playback</h3>

            {playbackError && (
              <div className="bg-red-900/30 border border-red-700 rounded p-3 mb-4">
                <p className="text-red-200 text-sm">{playbackError}</p>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Environment</label>
                <select
                  className="input w-full"
                  value={selectedEnvId}
                  onChange={(e) => handleEnvChange(e.target.value)}
                >
                  {environments.map((env) => (
                    <option key={env.id} value={env.id}>
                      {env.name} ({env.base_url})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Browser</label>
                <select
                  className="input w-full"
                  value={selectedBrowser}
                  onChange={(e) => setSelectedBrowser(e.target.value)}
                  disabled={availableBrowsers.length === 0}
                >
                  {availableBrowsers.length > 0 ? (
                    availableBrowsers.map((bc) => (
                      <option key={bc.id} value={bc.browser}>
                        {bc.browser.charAt(0).toUpperCase() + bc.browser.slice(1)}
                      </option>
                    ))
                  ) : (
                    <option value="">No browsers configured</option>
                  )}
                </select>
                {availableBrowsers.length === 0 && (
                  <p className="text-xs text-red-400 mt-1">
                    Add browser configs in Environment settings
                  </p>
                )}
              </div>

              <div className="bg-gray-700/30 rounded p-3 text-sm">
                <p className="text-gray-400">
                  <strong>Viewport:</strong> {currentSession.viewport_width}×
                  {currentSession.viewport_height}
                </p>
                <p className="text-gray-400">
                  <strong>Steps:</strong> {events.length} events to replay
                </p>
                <p className="text-gray-400">
                  <strong>Screenshots:</strong> {events.filter((e) => e.should_screenshot).length}{' '}
                  marked + failures
                </p>
              </div>
            </div>

            <div className="flex gap-3 justify-end mt-6">
              <button
                onClick={() => setShowPlaybackModal(false)}
                className="btn btn-secondary"
                disabled={startingPlayback}
              >
                Cancel
              </button>
              <button
                onClick={handleStartPlayback}
                className="btn btn-primary"
                disabled={startingPlayback || !selectedEnvId}
              >
                {startingPlayback ? 'Starting...' : 'Start Playback'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
