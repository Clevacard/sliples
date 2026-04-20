import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useRecordingsStore } from '../store/recordings'
import { RecordedEvent, EventMetadataUpdate } from '../api/client'
import Modal from './Modal'
import KeyValueEditor, { KeyValuePair } from './KeyValueEditor'

interface EditEventModalProps {
  event: RecordedEvent
  onClose: () => void
}

export default function EditEventModal({ event, onClose }: EditEventModalProps) {
  const { id: sessionId } = useParams<{ id: string }>()
  const { updateEvent } = useRecordingsStore()
  const [stepLabel, setStepLabel] = useState(event.step_label || '')
  const [shouldScreenshot, setShouldScreenshot] = useState(event.should_screenshot || false)
  const [parameters, setParameters] = useState<Record<string, string>>(event.parameters || {})
  const [notes, setNotes] = useState(event.notes || '')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async () => {
    if (!sessionId) return

    setIsSaving(true)
    setError(null)

    try {
      const data: EventMetadataUpdate = {
        step_label: stepLabel || undefined,
        should_screenshot: shouldScreenshot,
        parameters: Object.keys(parameters).length > 0 ? parameters : undefined,
        notes: notes || undefined,
      }

      await updateEvent(sessionId, event.id, data)
      onClose()
    } catch (err: any) {
      setError(err.message || 'Failed to save changes')
    } finally {
      setIsSaving(false)
    }
  }

  const handleParameterChange = (pairs: KeyValuePair[]) => {
    const newParams = pairs.reduce(
      (acc, pair) => {
        if (pair.key) acc[pair.key] = pair.value
        return acc
      },
      {} as Record<string, string>,
    )
    setParameters(newParams)
  }

  return (
    <Modal isOpen={true} onClose={onClose} title={`Edit Step ${event.sequence}`} size="lg">
      <div className="space-y-6">
        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded p-3">
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        {/* Step Label */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Step Label</label>
          <input
            type="text"
            className="input w-full"
            placeholder="e.g., Enter email, Click submit, etc."
            value={stepLabel}
            onChange={(e) => setStepLabel(e.target.value)}
          />
          <p className="text-xs text-gray-500 mt-1">Human-readable name for this step</p>
        </div>

        {/* Should Screenshot */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="should_screenshot"
            checked={shouldScreenshot}
            onChange={(e) => setShouldScreenshot(e.target.checked)}
            className="w-4 h-4 accent-blue-600"
          />
          <label htmlFor="should_screenshot" className="text-sm font-medium text-gray-300">
            📷 Mark for screenshot
          </label>
          <p className="text-xs text-gray-500">Take a screenshot at this step during playback</p>
        </div>

        {/* Parameters */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Parameters (Parametrize)</label>
          <div className="bg-gray-700/20 rounded p-4 mb-2">
            <p className="text-xs text-gray-400 mb-3">
              Extract values into parameters that can be reused across steps. Format: param_name = variable_name
            </p>
            <KeyValueEditor
              pairs={Object.entries(parameters).map(([key, value]) => ({ key, value }))}
              onChange={handleParameterChange}
              keyPlaceholder="e.g., username"
              valuePlaceholder="e.g., USER_EMAIL"
            />
          </div>
          <p className="text-xs text-gray-500">
            Example: parameter "email" with variable "USER_EMAIL" becomes ${'{'}USER_EMAIL{'}'}
          </p>
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Notes</label>
          <textarea
            className="input w-full h-24 resize-none"
            placeholder="Add any additional notes or context about this step..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        {/* Event Context */}
        <div className="bg-gray-700/20 rounded p-4">
          <h4 className="text-xs font-semibold text-gray-400 mb-3">Event Context</h4>
          <div className="space-y-2 text-xs">
            <div>
              <span className="text-gray-500">Type:</span>
              <span className="text-gray-300 ml-2">{event.event_type}</span>
            </div>
            {event.selector_test_id && (
              <div>
                <span className="text-gray-500">Test ID:</span>
                <span className="text-gray-300 ml-2">{event.selector_test_id}</span>
              </div>
            )}
            {event.label_text && (
              <div>
                <span className="text-gray-500">Label:</span>
                <span className="text-gray-300 ml-2">{event.label_text}</span>
              </div>
            )}
            {event.value && (
              <div>
                <span className="text-gray-500">Value:</span>
                <span className="text-gray-300 ml-2 font-mono">{event.value}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex gap-3 justify-end mt-8 pt-6 border-t border-gray-700">
        <button
          onClick={onClose}
          className="btn btn-secondary"
          disabled={isSaving}
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          className="btn btn-primary"
          disabled={isSaving}
        >
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </Modal>
  )
}
