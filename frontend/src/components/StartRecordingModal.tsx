import { useState } from 'react'
import { useProjectsStore } from '../store/projects'
import { useRecordingsStore } from '../store/recordings'
import Modal, { ModalFooter } from './Modal'

interface StartRecordingModalProps {
  isOpen: boolean
  onClose: () => void
  onRecordingStarted?: () => void
}

interface ApiKeyResponse {
  id: string
  key: string
  key_prefix: string
  name: string
  created_at: string
}

interface RecordingStarted {
  session_id: string
  name: string
  status: string
}

export default function StartRecordingModal({
  isOpen,
  onClose,
  onRecordingStarted,
}: StartRecordingModalProps) {
  const { currentProject } = useProjectsStore()
  const { fetchSessions } = useRecordingsStore()

  const [step, setStep] = useState<'form' | 'snippet' | 'started'>('form')
  const [recordingName, setRecordingName] = useState('')
  const [recordingUrl, setRecordingUrl] = useState('')
  const [keyName, setKeyName] = useState(`recorder-${new Date().toISOString().split('T')[0]}`)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generatedKey, setGeneratedKey] = useState<ApiKeyResponse | null>(null)
  const [startedRecording, setStartedRecording] = useState<RecordingStarted | null>(null)
  const [snippetCode, setSnippetCode] = useState('')

  const handleGenerateKey = async () => {
    if (!keyName.trim()) {
      setError('API key name is required')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/v1/auth/keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: keyName,
          project_id: currentProject?.id,
        }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to generate API key')
      }

      const key: ApiKeyResponse = await response.json()
      setGeneratedKey(key)
    } catch (err: any) {
      setError(err.message || 'Failed to generate API key')
    } finally {
      setIsLoading(false)
    }
  }

  const handleStartRecording = async () => {
    if (!recordingName.trim() || !recordingUrl.trim() || !generatedKey) {
      setError('Recording name, URL, and API key are required')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/v1/recorder/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': generatedKey.key,
        },
        body: JSON.stringify({
          name: recordingName,
          url: recordingUrl,
          user_agent: navigator.userAgent,
          viewport_width: window.innerWidth,
          viewport_height: window.innerHeight,
        }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to start recording')
      }

      const recording: RecordingStarted = await response.json()
      setStartedRecording(recording)

      // Generate snippet code
      const endpoint = window.location.origin
      const snippetUrl = `/api/v1/recorder/snippet.js?api_key=${generatedKey.key}&endpoint=${encodeURIComponent(endpoint)}&project_id=${currentProject?.id || ''}`
      setSnippetCode(`<!-- Sliples Recorder Snippet -->
<script src="${snippetUrl}"></script>
<script>
  // Start recording
  SliplesRecorder.init({
    sessionId: '${recording.session_id}',
    endpoint: '${endpoint}',
    apiKey: '${generatedKey.key}'
  });

  // When done recording, call:
  // SliplesRecorder.stop();
</script>`)

      setStep('snippet')
      await fetchSessions()
      onRecordingStarted?.()
    } catch (err: any) {
      setError(err.message || 'Failed to start recording')
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    setStep('form')
    setRecordingName('')
    setRecordingUrl('')
    setKeyName(`recorder-${new Date().toISOString().split('T')[0]}`)
    setError(null)
    setGeneratedKey(null)
    setStartedRecording(null)
    setSnippetCode('')
    onClose()
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Start Recording" size="lg">
      <div className="space-y-4 pb-12">
        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded p-3">
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        {step === 'form' && (
          <>
            {/* Step 1: Generate API Key */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-300">Step 1: Generate API Key</h3>
              {!generatedKey ? (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">API Key Name</label>
                    <input
                      type="text"
                      className="input w-full"
                      placeholder="e.g., recorder-2026-04-20"
                      value={keyName}
                      onChange={(e) => setKeyName(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>
                  <button
                    onClick={handleGenerateKey}
                    className="btn btn-primary w-full"
                    disabled={isLoading || !keyName.trim()}
                  >
                    {isLoading ? 'Generating...' : 'Generate API Key'}
                  </button>
                </>
              ) : (
                <div className="space-y-2">
                  <div className="bg-green-900/20 border border-green-700 rounded p-3">
                    <p className="text-green-200 text-sm mb-1">✓ API Key generated successfully</p>
                    <p className="text-xs text-gray-400">Save this key securely. You won't see it again.</p>
                  </div>
                  <div className="bg-gray-900 border border-gray-700 rounded p-3 relative">
                    <pre className="text-xs text-gray-300 font-mono break-all">
                      {generatedKey.key}
                    </pre>
                    <button
                      onClick={() => copyToClipboard(generatedKey.key)}
                      className="absolute top-2 right-2 btn btn-sm bg-blue-600 hover:bg-blue-700 text-white text-xs"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              )}
            </div>

            {generatedKey && (
              <>
                {/* Step 2: Recording Details */}
                <div className="space-y-3 pt-4 border-t border-gray-700">
                  <h3 className="text-sm font-semibold text-gray-300">Step 2: Recording Details</h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">Recording Name</label>
                    <input
                      type="text"
                      className="input w-full"
                      placeholder="e.g., Login flow, Checkout process"
                      value={recordingName}
                      onChange={(e) => setRecordingName(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">Website URL</label>
                    <input
                      type="url"
                      className="input w-full"
                      placeholder="https://example.com"
                      value={recordingUrl}
                      onChange={(e) => setRecordingUrl(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>
                </div>
              </>
            )}

            {/* Footer */}
            <ModalFooter>
              <button onClick={handleClose} className="btn btn-secondary" disabled={isLoading}>
                Cancel
              </button>
              <button
                onClick={handleStartRecording}
                className="btn btn-primary"
                disabled={isLoading || !generatedKey || !recordingName.trim() || !recordingUrl.trim()}
              >
                {isLoading ? 'Starting...' : 'Start Recording'}
              </button>
            </ModalFooter>
          </>
        )}

        {step === 'snippet' && startedRecording && (
          <>
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-300">Step 3: Add Snippet to Website</h3>
              <p className="text-sm text-gray-400">
                Copy the code below and paste it into your website's HTML <code className="bg-gray-800 px-1 rounded text-xs">&lt;head&gt;</code> tag:
              </p>

              <div className="bg-gray-900 border border-gray-700 rounded p-3 relative">
                <pre className="text-xs text-gray-300 overflow-x-auto whitespace-pre-wrap break-words font-mono">
                  {snippetCode}
                </pre>
                <button
                  onClick={() => copyToClipboard(snippetCode)}
                  className="absolute top-2 right-2 btn btn-sm bg-blue-600 hover:bg-blue-700 text-white text-xs"
                >
                  Copy
                </button>
              </div>

              <div className="bg-blue-900/20 border border-blue-700 rounded p-3">
                <p className="text-blue-200 text-sm">
                  <strong>Session ID:</strong> {startedRecording.session_id}
                </p>
                <p className="text-blue-200 text-sm mt-1">
                  <strong>Status:</strong> {startedRecording.status}
                </p>
              </div>

              <div className="bg-yellow-900/20 border border-yellow-700 rounded p-3">
                <p className="text-yellow-200 text-sm">
                  When you're done recording, call <code className="bg-yellow-900 px-1 rounded text-xs">SliplesRecorder.stop()</code> in the browser console.
                </p>
              </div>
            </div>

            {/* Footer */}
            <ModalFooter>
              <button onClick={handleClose} className="btn btn-primary w-full">
                Done
              </button>
            </ModalFooter>
          </>
        )}
      </div>
    </Modal>
  )
}
