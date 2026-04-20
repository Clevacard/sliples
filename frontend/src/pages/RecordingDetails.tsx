import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useRecordingsStore } from '../store/recordings'
import EditEventModal from '../components/EditEventModal'
import { RecordedEvent } from '../api/client'

export default function RecordingDetails() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { currentSession, events, isLoading, error, fetchSessionDetails } = useRecordingsStore()
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null)
  const [editingEvent, setEditingEvent] = useState<RecordedEvent | null>(null)

  useEffect(() => {
    if (id) {
      fetchSessionDetails(id)
    }
  }, [id, fetchSessionDetails])

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
          <span className={`badge ${currentSession.status === 'stopped' ? 'badge-success' : 'badge-info'}`}>
            {currentSession.status}
          </span>
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
            <p className="text-2xl font-bold text-white">{events.filter((e) => e.should_screenshot).length}</p>
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

      {/* Events List */}
      {events.length > 0 ? (
        <div className="space-y-3">
          {events.map((event) => (
            <div key={event.id} className="card">
              <button
                onClick={() => setExpandedEventId(expandedEventId === event.id ? null : event.id)}
                className="w-full text-left flex items-center justify-between hover:bg-gray-700/30 p-3 -m-3 p-4 rounded"
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
                        <span className="text-xs bg-blue-900/30 text-blue-300 px-2 py-1 rounded">📷 Screenshot</span>
                      )}
                      {event.parameters && Object.keys(event.parameters).length > 0 && (
                        <span className="text-xs bg-green-900/30 text-green-300 px-2 py-1 rounded">
                          🔧 {Object.keys(event.parameters).length} param(s)
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
                <div className="text-gray-400">
                  {expandedEventId === event.id ? '▼' : '▶'}
                </div>
              </button>

              {/* Expanded Details */}
              {expandedEventId === event.id && (
                <div className="border-t border-gray-700 mt-4 pt-4 space-y-4">
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
                          <span className="text-gray-200 ml-2 font-mono text-xs break-all">{event.selector_css}</span>
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
        <div className="card text-center py-12">
          <p className="text-gray-400">No events recorded</p>
        </div>
      )}

      {/* Edit Modal */}
      {editingEvent && <EditEventModal event={editingEvent} onClose={() => setEditingEvent(null)} />}
    </div>
  )
}
