import { useState, useEffect, useCallback, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import StepExecutor from '../components/StepExecutor'
import Modal from '../components/Modal'
import {
  getEnvironments,
  getScenarios,
  startTestSession,
  loadScenarioIntoSession,
  executeStep,
  skipStep,
  takeScreenshot,
  getSessionStatus,
  endTestSession,
  pauseSession,
  resumeSession,
  navigateSession,
  runCustomAction,
  TestSession,
  StepExecuteResponse,
  Environment,
} from '../api/client'

interface Scenario {
  id: string
  name: string
  tags: string[]
  feature_path: string
}

interface Step {
  index: number
  keyword: string
  text: string
  full: string
  status: 'pending' | 'passed' | 'failed' | 'skipped' | 'error' | 'running'
}

interface StepResult {
  step_index: number
  step_name: string
  status: string
  duration_ms: number
  error_message: string | null
  executed_at: string
}

export default function TestMode() {
  const [searchParams] = useSearchParams()

  // Data state
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [session, setSession] = useState<TestSession | null>(null)
  const [steps, setSteps] = useState<Step[]>([])
  const [stepResults, setStepResults] = useState<StepResult[]>([])
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [screenshot, setScreenshot] = useState<string | null>(null)
  const [logs, setLogs] = useState<string[]>([])

  // UI state
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [selectedEnvironment, setSelectedEnvironment] = useState<string>('')
  const [selectedScenario, setSelectedScenario] = useState<string>('')
  const [selectedBrowser, setSelectedBrowser] = useState<string>('chromium')

  // Modal state
  const [showScreenshotModal, setShowScreenshotModal] = useState(false)
  const [showCustomActionModal, setShowCustomActionModal] = useState(false)
  const [showNavigateModal, setShowNavigateModal] = useState(false)
  const [showSessionTerminatedModal, setShowSessionTerminatedModal] = useState(false)
  const [customAction, setCustomAction] = useState({ action: 'click', selector: '', value: '' })
  const [navigateUrl, setNavigateUrl] = useState('')

  // Screenshot gallery
  const [screenshotGallery, setScreenshotGallery] = useState<string[]>([])

  // Polling interval ref
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Load environments and scenarios on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const [envs, scens] = await Promise.all([getEnvironments(), getScenarios()])
        setEnvironments(envs)
        setScenarios(scens)

        // Pre-select from URL params
        const envParam = searchParams.get('environment')
        const scenParam = searchParams.get('scenario')
        if (envParam) setSelectedEnvironment(envParam)
        if (scenParam) setSelectedScenario(scenParam)
      } catch (err) {
        setError('Failed to load data')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [searchParams])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

  // Start polling when session is active
  useEffect(() => {
    if (session && session.status === 'active') {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const status = await getSessionStatus(session.id)
          setStepResults(status.step_results)
          setCurrentStepIndex(status.current_step_index)
          setLogs(status.logs)
        } catch (err: unknown) {
          // Detect session termination (404 = session not found)
          const isNotFound =
            (err as { response?: { status?: number } })?.response?.status === 404 ||
            (err instanceof Error && err.message.includes('404'))
          if (isNotFound) {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current)
              pollIntervalRef.current = null
            }
            setShowSessionTerminatedModal(true)
          }
        }
      }, 3000)
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
    }
  }, [session?.id, session?.status])

  // Start a new test session
  const handleStartSession = async () => {
    if (!selectedEnvironment) {
      setError('Please select an environment')
      return
    }

    setStarting(true)
    setError(null)

    try {
      const newSession = await startTestSession({
        environment_id: selectedEnvironment,
        scenario_id: selectedScenario || undefined,
        browser_type: selectedBrowser,
      })

      setSession(newSession)
      setScreenshot(null)
      setScreenshotGallery([])
      setLogs([])

      // If scenario was selected, load it
      if (selectedScenario) {
        const scenarioData = await loadScenarioIntoSession(newSession.id, {
          scenario_id: selectedScenario,
        })
        setSteps(scenarioData.steps as Step[])
        setCurrentStepIndex(0)
        setStepResults([])
      }

      // Take initial screenshot
      const initialScreenshot = await takeScreenshot(newSession.id)
      setScreenshot(initialScreenshot.screenshot_base64)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start session'
      setError(message)
    } finally {
      setStarting(false)
    }
  }

  // End the current session
  const handleEndSession = async () => {
    if (!session) return

    try {
      await endTestSession(session.id)
      setSession(null)
      setSteps([])
      setStepResults([])
      setCurrentStepIndex(0)
      setScreenshot(null)
      setScreenshotGallery([])
      setLogs([])
    } catch (err) {
      setError('Failed to end session')
    }
  }

  // Restart the current session (end and start fresh with same settings)
  const handleRestartSession = async () => {
    if (!session) return

    setStarting(true)
    setError(null)

    try {
      // End current session silently
      try {
        await endTestSession(session.id)
      } catch {
        // Ignore errors when ending (session might already be gone)
      }

      // Reset state
      setSession(null)
      setSteps([])
      setStepResults([])
      setCurrentStepIndex(0)
      setScreenshot(null)
      setScreenshotGallery([])
      setLogs([])

      // Start new session with same settings
      const newSession = await startTestSession({
        environment_id: selectedEnvironment,
        scenario_id: selectedScenario || undefined,
        browser_type: selectedBrowser,
      })

      setSession(newSession)

      // If scenario was selected, load it
      if (selectedScenario) {
        const scenarioData = await loadScenarioIntoSession(newSession.id, {
          scenario_id: selectedScenario,
        })
        setSteps(scenarioData.steps as Step[])
      }

      // Take initial screenshot
      const initialScreenshot = await takeScreenshot(newSession.id)
      setScreenshot(initialScreenshot.screenshot_base64)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to restart session'
      setError(message)
    } finally {
      setStarting(false)
    }
  }

  // Switch to a different environment (restart session with new environment)
  const handleSwitchEnvironment = async (newEnvironmentId: string) => {
    if (!session) return

    setStarting(true)
    setError(null)

    try {
      // End current session silently
      try {
        await endTestSession(session.id)
      } catch {
        // Ignore errors when ending
      }

      // Reset state
      setSession(null)
      setSteps([])
      setStepResults([])
      setCurrentStepIndex(0)
      setScreenshot(null)
      setScreenshotGallery([])
      setLogs([])

      // Start new session with new environment
      const newSession = await startTestSession({
        environment_id: newEnvironmentId,
        scenario_id: selectedScenario || undefined,
        browser_type: selectedBrowser,
      })

      setSession(newSession)

      // If scenario was selected, load it
      if (selectedScenario) {
        const scenarioData = await loadScenarioIntoSession(newSession.id, {
          scenario_id: selectedScenario,
        })
        setSteps(scenarioData.steps as Step[])
      }

      // Take initial screenshot
      const initialScreenshot = await takeScreenshot(newSession.id)
      setScreenshot(initialScreenshot.screenshot_base64)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to switch environment'
      setError(message)
    } finally {
      setStarting(false)
    }
  }

  // Execute a single step
  const handleExecuteStep = useCallback(
    async (stepIndex?: number) => {
      if (!session || executing) return

      setExecuting(true)
      setError(null)

      try {
        const result = await executeStep(session.id, stepIndex)
        handleStepResult(result)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to execute step'
        setError(message)
      } finally {
        setExecuting(false)
      }
    },
    [session, executing]
  )

  // Handle step execution result
  const handleStepResult = (result: StepExecuteResponse) => {
    setCurrentStepIndex(result.next_step_index)

    // Add to results
    setStepResults((prev) => [
      ...prev,
      {
        step_index: result.next_step_index - 1,
        step_name: result.step_name,
        status: result.status,
        duration_ms: result.duration_ms,
        error_message: result.error_message,
        executed_at: new Date().toISOString(),
      },
    ])

    // Update screenshot
    if (result.screenshot_base64) {
      setScreenshot(result.screenshot_base64)
      setScreenshotGallery((prev) => [...prev, result.screenshot_base64!])
    }
  }

  // Skip the current step
  const handleSkipStep = async () => {
    if (!session || executing) return

    setExecuting(true)
    try {
      const result = await skipStep(session.id)
      handleStepResult(result)
    } catch (err) {
      setError('Failed to skip step')
    } finally {
      setExecuting(false)
    }
  }

  // Run all remaining steps
  const handleRunAll = async () => {
    if (!session || executing) return

    setExecuting(true)
    try {
      for (let i = currentStepIndex; i < steps.length; i++) {
        const result = await executeStep(session.id)
        handleStepResult(result)

        // Stop if step failed
        if (result.status === 'failed' || result.status === 'error') {
          break
        }
      }
    } catch (err) {
      setError('Failed to run all steps')
    } finally {
      setExecuting(false)
    }
  }

  // Take a manual screenshot
  const handleTakeScreenshot = async () => {
    if (!session) return

    try {
      const result = await takeScreenshot(session.id)
      setScreenshot(result.screenshot_base64)
      setScreenshotGallery((prev) => [...prev, result.screenshot_base64])
    } catch (err) {
      setError('Failed to take screenshot')
    }
  }

  // Navigate to URL
  const handleNavigate = async () => {
    if (!session || !navigateUrl) return

    setExecuting(true)
    try {
      const result = await navigateSession(session.id, navigateUrl)
      if (result.screenshot_base64) {
        setScreenshot(result.screenshot_base64)
        setScreenshotGallery((prev) => [...prev, result.screenshot_base64!])
      }
      setShowNavigateModal(false)
      setNavigateUrl('')
    } catch (err) {
      setError('Failed to navigate')
    } finally {
      setExecuting(false)
    }
  }

  // Run custom action
  const handleCustomAction = async () => {
    if (!session) return

    setExecuting(true)
    try {
      const result = await runCustomAction(
        session.id,
        customAction.action,
        customAction.selector,
        customAction.value
      )
      if (result.screenshot_base64) {
        setScreenshot(result.screenshot_base64)
        setScreenshotGallery((prev) => [...prev, result.screenshot_base64!])
      }
      setShowCustomActionModal(false)
      setCustomAction({ action: 'click', selector: '', value: '' })
    } catch (err) {
      setError('Failed to run action')
    } finally {
      setExecuting(false)
    }
  }

  // Load a different scenario into the session
  const handleLoadScenario = async (scenarioId: string) => {
    if (!session) return

    try {
      const scenarioData = await loadScenarioIntoSession(session.id, {
        scenario_id: scenarioId,
      })
      setSteps(scenarioData.steps as Step[])
      setCurrentStepIndex(0)
      setStepResults([])
      setSelectedScenario(scenarioId)
    } catch (err) {
      setError('Failed to load scenario')
    }
  }

  // Pause/Resume session
  const handlePauseResume = async () => {
    if (!session) return

    try {
      if (session.status === 'active') {
        await pauseSession(session.id)
        setSession({ ...session, status: 'paused' })
      } else if (session.status === 'paused') {
        await resumeSession(session.id)
        setSession({ ...session, status: 'active' })
      }
    } catch (err) {
      setError('Failed to pause/resume session')
    }
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-center">
          <svg
            className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3"
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
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      {/* Error banner */}
      {error && (
        <div className="bg-red-900/50 border-b border-red-700 text-red-200 px-4 py-2 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
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

      {!session ? (
        // Session setup form
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="card max-w-lg w-full">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-blue-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-100">Interactive Test Mode</h1>
              <p className="text-gray-400 mt-2">
                Run tests step-by-step with a live browser preview
              </p>
            </div>

            <div className="space-y-4">
              {/* Environment selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Environment *
                </label>
                <select
                  value={selectedEnvironment}
                  onChange={(e) => setSelectedEnvironment(e.target.value)}
                  className="input w-full"
                >
                  <option value="">Select an environment</option>
                  {environments.map((env) => (
                    <option key={env.id} value={env.id}>
                      {env.name} ({env.base_url})
                    </option>
                  ))}
                </select>
              </div>

              {/* Scenario selection (optional) */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Scenario (optional)
                </label>
                <select
                  value={selectedScenario}
                  onChange={(e) => setSelectedScenario(e.target.value)}
                  className="input w-full"
                >
                  <option value="">Start without a scenario</option>
                  {scenarios.map((scenario) => (
                    <option key={scenario.id} value={scenario.id}>
                      {scenario.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  You can load a scenario after starting the session
                </p>
              </div>

              {/* Browser selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Browser</label>
                <select
                  value={selectedBrowser}
                  onChange={(e) => setSelectedBrowser(e.target.value)}
                  className="input w-full"
                >
                  <option value="chromium">Chromium</option>
                  <option value="firefox">Firefox</option>
                  <option value="webkit">WebKit (Safari)</option>
                </select>
              </div>

              {/* Start button */}
              <button
                onClick={handleStartSession}
                disabled={starting || !selectedEnvironment}
                className="btn btn-primary w-full mt-6"
              >
                {starting ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
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
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    Starting Browser...
                  </span>
                ) : (
                  'Start Test Session'
                )}
              </button>
            </div>
          </div>
        </div>
      ) : (
        // Active session view - Split layout
        <div className="flex-1 flex overflow-hidden">
          {/* Left panel - Controls */}
          <div className="w-96 border-r border-gray-700 flex flex-col bg-gray-800">
            {/* Session info header */}
            <div className="p-4 border-b border-gray-700">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-semibold text-gray-100">Test Session</h2>
                <div className="flex items-center gap-2">
                  <span
                    className={`badge ${
                      session.status === 'active' ? 'badge-success' : 'badge-warning'
                    }`}
                  >
                    {session.status}
                  </span>
                </div>
              </div>

              <div className="text-sm text-gray-400 space-y-1">
                <p>
                  <span className="text-gray-500">Environment:</span> {session.environment_name}
                </p>
                <p>
                  <span className="text-gray-500">Browser:</span> {session.browser_type}
                </p>
                {session.scenario_name && (
                  <p>
                    <span className="text-gray-500">Scenario:</span> {session.scenario_name}
                  </p>
                )}
              </div>

              {/* Session controls */}
              <div className="flex gap-2 mt-4">
                <button
                  onClick={handleRestartSession}
                  disabled={starting}
                  className="btn btn-secondary btn-sm flex-1"
                  title="Restart session with same settings"
                >
                  {starting ? (
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  )}
                </button>
                <button
                  onClick={handlePauseResume}
                  className="btn btn-secondary btn-sm flex-1"
                >
                  {session.status === 'active' ? 'Pause' : 'Resume'}
                </button>
                <button onClick={handleEndSession} className="btn btn-sm bg-red-900 hover:bg-red-800 text-white flex-1">
                  End
                </button>
              </div>
            </div>

            {/* Environment switcher */}
            <div className="p-4 border-b border-gray-700">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Switch Environment
              </label>
              <select
                value={selectedEnvironment}
                onChange={(e) => {
                  if (e.target.value && e.target.value !== selectedEnvironment) {
                    setSelectedEnvironment(e.target.value)
                    // Auto-restart with new environment
                    handleSwitchEnvironment(e.target.value)
                  }
                }}
                disabled={starting}
                className="input w-full text-sm"
              >
                {environments.map((env) => (
                  <option key={env.id} value={env.id}>
                    {env.name} ({env.base_url})
                  </option>
                ))}
              </select>
            </div>

            {/* Scenario selector */}
            <div className="p-4 border-b border-gray-700">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Load Scenario
              </label>
              <select
                value={selectedScenario}
                onChange={(e) => e.target.value && handleLoadScenario(e.target.value)}
                className="input w-full text-sm"
              >
                <option value="">Select a scenario...</option>
                {scenarios.map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Step executor */}
            <div className="flex-1 overflow-hidden">
              <StepExecutor
                steps={steps}
                currentStepIndex={currentStepIndex}
                stepResults={stepResults}
                isExecuting={executing}
                onExecuteStep={handleExecuteStep}
                onSkipStep={handleSkipStep}
                onRunAll={handleRunAll}
              />
            </div>
          </div>

          {/* Right panel - Browser preview */}
          <div className="flex-1 flex flex-col bg-gray-900 overflow-hidden">
            {/* Preview toolbar */}
            <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
              <div className="flex items-center gap-4">
                <h3 className="font-medium text-gray-200">Browser Preview</h3>
                <span className="text-sm text-gray-500">
                  {session.environment_base_url}
                </span>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setShowNavigateModal(true)}
                  className="btn btn-sm btn-secondary"
                  title="Navigate to URL"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
                    />
                  </svg>
                </button>
                <button
                  onClick={() => setShowCustomActionModal(true)}
                  className="btn btn-sm btn-secondary"
                  title="Run custom action"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                    />
                  </svg>
                </button>
                <button
                  onClick={handleTakeScreenshot}
                  className="btn btn-sm btn-secondary"
                  title="Take screenshot"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                </button>
                <button
                  onClick={() => setShowScreenshotModal(true)}
                  disabled={screenshotGallery.length === 0}
                  className="btn btn-sm btn-secondary"
                  title="Screenshot gallery"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                  {screenshotGallery.length > 0 && (
                    <span className="ml-1 text-xs">{screenshotGallery.length}</span>
                  )}
                </button>
              </div>
            </div>

            {/* Screenshot preview */}
            <div className="flex-1 overflow-auto p-4 flex items-center justify-center bg-gray-950">
              {screenshot ? (
                <img
                  src={`data:image/png;base64,${screenshot}`}
                  alt="Browser screenshot"
                  className="max-w-full max-h-full rounded-lg shadow-2xl border border-gray-700"
                  style={{ imageRendering: 'crisp-edges' }}
                />
              ) : (
                <div className="text-center text-gray-500">
                  <svg
                    className="w-16 h-16 mx-auto mb-4 text-gray-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                  <p>Browser preview will appear here</p>
                  <p className="text-sm text-gray-600 mt-1">
                    Run a step or take a screenshot to see the browser state
                  </p>
                </div>
              )}
            </div>

            {/* Logs panel */}
            <div className="h-32 border-t border-gray-700 bg-gray-800">
              <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
                <h4 className="text-sm font-medium text-gray-300">Console Output</h4>
                <button
                  onClick={() => setLogs([])}
                  className="text-xs text-gray-500 hover:text-gray-400"
                >
                  Clear
                </button>
              </div>
              <div className="h-[calc(100%-2.5rem)] overflow-y-auto p-2 font-mono text-xs">
                {logs.length === 0 ? (
                  <p className="text-gray-600">Logs will appear here...</p>
                ) : (
                  logs.map((log, i) => (
                    <div
                      key={i}
                      className={`py-0.5 ${
                        log.includes('[ERROR]')
                          ? 'text-red-400'
                          : log.includes('[WARNING]')
                          ? 'text-yellow-400'
                          : 'text-gray-400'
                      }`}
                    >
                      {log}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigate Modal */}
      <Modal
        isOpen={showNavigateModal}
        onClose={() => setShowNavigateModal(false)}
        title="Navigate to URL"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">URL</label>
            <input
              type="text"
              value={navigateUrl}
              onChange={(e) => setNavigateUrl(e.target.value)}
              placeholder="https://example.com or /path"
              className="input w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Enter a full URL or a path relative to the base URL
            </p>
          </div>
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowNavigateModal(false)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleNavigate}
              disabled={!navigateUrl || executing}
              className="btn btn-primary"
            >
              Navigate
            </button>
          </div>
        </div>
      </Modal>

      {/* Custom Action Modal */}
      <Modal
        isOpen={showCustomActionModal}
        onClose={() => setShowCustomActionModal(false)}
        title="Run Custom Action"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Action</label>
            <select
              value={customAction.action}
              onChange={(e) => setCustomAction({ ...customAction, action: e.target.value })}
              className="input w-full"
            >
              <option value="click">Click</option>
              <option value="fill">Fill Input</option>
              <option value="select">Select Option</option>
              <option value="check">Check Checkbox</option>
              <option value="uncheck">Uncheck Checkbox</option>
              <option value="hover">Hover</option>
              <option value="press">Press Key</option>
              <option value="type">Type Text</option>
              <option value="wait">Wait (seconds)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Selector {customAction.action !== 'wait' && customAction.action !== 'type' && '(CSS)'}
            </label>
            <input
              type="text"
              value={customAction.selector}
              onChange={(e) => setCustomAction({ ...customAction, selector: e.target.value })}
              placeholder={customAction.action === 'wait' ? '' : '#element-id or .class-name'}
              className="input w-full"
              disabled={customAction.action === 'wait' || customAction.action === 'type'}
            />
          </div>
          {(customAction.action === 'fill' ||
            customAction.action === 'select' ||
            customAction.action === 'press' ||
            customAction.action === 'type' ||
            customAction.action === 'wait') && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {customAction.action === 'wait'
                  ? 'Seconds'
                  : customAction.action === 'press'
                  ? 'Key (e.g., Enter, Tab)'
                  : 'Value'}
              </label>
              <input
                type="text"
                value={customAction.value}
                onChange={(e) => setCustomAction({ ...customAction, value: e.target.value })}
                placeholder={customAction.action === 'wait' ? '1' : ''}
                className="input w-full"
              />
            </div>
          )}
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowCustomActionModal(false)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleCustomAction}
              disabled={executing}
              className="btn btn-primary"
            >
              Run Action
            </button>
          </div>
        </div>
      </Modal>

      {/* Screenshot Gallery Modal */}
      <Modal
        isOpen={showScreenshotModal}
        onClose={() => setShowScreenshotModal(false)}
        title={`Screenshot Gallery (${screenshotGallery.length})`}
        size="full"
      >
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-h-[70vh] overflow-y-auto">
          {screenshotGallery.map((ss, index) => (
            <div key={index} className="relative group">
              <img
                src={`data:image/png;base64,${ss}`}
                alt={`Screenshot ${index + 1}`}
                className="w-full rounded-lg border border-gray-700 cursor-pointer hover:border-blue-500 transition-colors"
                onClick={() => {
                  setScreenshot(ss)
                  setShowScreenshotModal(false)
                }}
              />
              <span className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                #{index + 1}
              </span>
            </div>
          ))}
        </div>
      </Modal>

      {/* Session Terminated Modal */}
      <Modal
        isOpen={showSessionTerminatedModal}
        onClose={() => {
          setShowSessionTerminatedModal(false)
          setSession(null)
          setSteps([])
          setStepResults([])
          setCurrentStepIndex(0)
          setScreenshot(null)
          setLogs([])
        }}
        title="Session Terminated"
      >
        <div className="text-center py-4">
          <div className="w-16 h-16 bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-100 mb-2">
            Test Session Ended
          </h3>
          <p className="text-gray-400 mb-6">
            The test session has been terminated. This may happen if the backend
            was restarted or the session timed out.
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => {
                setShowSessionTerminatedModal(false)
                setSession(null)
                setSteps([])
                setStepResults([])
                setCurrentStepIndex(0)
                setScreenshot(null)
                setLogs([])
              }}
              className="btn btn-secondary"
            >
              Close
            </button>
            <button
              onClick={() => {
                setShowSessionTerminatedModal(false)
                setSession(null)
                setSteps([])
                setStepResults([])
                setCurrentStepIndex(0)
                setScreenshot(null)
                setLogs([])
                // Trigger new session start
                handleStartSession()
              }}
              className="btn btn-primary"
            >
              Start New Session
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
