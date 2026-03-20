import { useState } from 'react'

// Types
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

interface StepExecutorProps {
  steps: Step[]
  currentStepIndex: number
  stepResults: StepResult[]
  isExecuting: boolean
  onExecuteStep: (stepIndex?: number) => void
  onSkipStep: () => void
  onRunAll: () => void
}

// Status icon component
const StatusIcon = ({ status, size = 'sm' }: { status: string; size?: 'sm' | 'md' }) => {
  const sizeClass = size === 'md' ? 'w-5 h-5' : 'w-4 h-4'

  switch (status) {
    case 'passed':
      return (
        <svg className={sizeClass} fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
      )
    case 'failed':
    case 'error':
      return (
        <svg className={sizeClass} fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clipRule="evenodd"
          />
        </svg>
      )
    case 'running':
      return (
        <svg className={`${sizeClass} animate-spin`} fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )
    case 'skipped':
      return (
        <svg className={sizeClass} fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z"
            clipRule="evenodd"
          />
        </svg>
      )
    default: // pending
      return (
        <svg className={sizeClass} fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
            clipRule="evenodd"
          />
        </svg>
      )
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'passed':
      return 'text-green-400'
    case 'failed':
    case 'error':
      return 'text-red-400'
    case 'running':
      return 'text-yellow-400'
    case 'skipped':
      return 'text-gray-400'
    default:
      return 'text-gray-500'
  }
}

const getKeywordColor = (keyword: string) => {
  switch (keyword) {
    case 'Given':
      return 'text-blue-400'
    case 'When':
      return 'text-purple-400'
    case 'Then':
      return 'text-green-400'
    case 'And':
    case 'But':
      return 'text-gray-400'
    default:
      return 'text-gray-400'
  }
}

const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`
}

export default function StepExecutor({
  steps,
  currentStepIndex,
  stepResults,
  isExecuting,
  onExecuteStep,
  onSkipStep,
  onRunAll,
}: StepExecutorProps) {
  const [expandedError, setExpandedError] = useState<number | null>(null)

  // Get result for a step
  const getStepResult = (stepIndex: number): StepResult | undefined => {
    return stepResults.find((r) => r.step_index === stepIndex)
  }

  // Get effective status for a step
  const getEffectiveStatus = (step: Step): string => {
    if (step.index === currentStepIndex && isExecuting) return 'running'
    const result = getStepResult(step.index)
    if (result) return result.status
    return step.status
  }

  // Calculate progress
  const completedSteps = stepResults.length
  const progress = steps.length > 0 ? (completedSteps / steps.length) * 100 : 0
  const passedSteps = stepResults.filter((r) => r.status === 'passed').length
  const failedSteps = stepResults.filter((r) => r.status === 'failed' || r.status === 'error').length

  return (
    <div className="flex flex-col h-full">
      {/* Header with controls */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-100">Test Steps</h3>
          <div className="flex gap-2">
            <button
              onClick={() => onExecuteStep()}
              disabled={isExecuting || currentStepIndex >= steps.length}
              className="btn btn-primary btn-sm flex items-center gap-2"
            >
              {isExecuting ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
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
                  Running...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  Run Step
                </>
              )}
            </button>
            <button
              onClick={onSkipStep}
              disabled={isExecuting || currentStepIndex >= steps.length}
              className="btn btn-secondary btn-sm"
              title="Skip current step"
            >
              Skip
            </button>
            <button
              onClick={onRunAll}
              disabled={isExecuting || currentStepIndex >= steps.length}
              className="btn btn-secondary btn-sm"
              title="Run all remaining steps"
            >
              Run All
            </button>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-2">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>
              Progress: {completedSteps} / {steps.length} steps
            </span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="progress-bar h-2">
            <div
              className="h-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="flex gap-4 text-sm">
          <span className="text-green-400">
            <StatusIcon status="passed" /> {passedSteps} passed
          </span>
          <span className="text-red-400">
            <StatusIcon status="failed" /> {failedSteps} failed
          </span>
          <span className="text-gray-400">
            <StatusIcon status="pending" /> {steps.length - completedSteps} remaining
          </span>
        </div>
      </div>

      {/* Steps list */}
      <div className="flex-1 overflow-y-auto">
        {steps.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <svg
                className="w-12 h-12 mx-auto mb-3 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              <p>No scenario loaded</p>
              <p className="text-sm text-gray-600">Select a scenario to begin testing</p>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {steps.map((step) => {
              const effectiveStatus = getEffectiveStatus(step)
              const result = getStepResult(step.index)
              const isCurrent = step.index === currentStepIndex
              const hasError = result?.error_message

              return (
                <div
                  key={step.index}
                  className={`
                    p-3 transition-colors
                    ${isCurrent ? 'bg-blue-900/20 border-l-2 border-blue-500' : ''}
                    ${effectiveStatus === 'passed' ? 'bg-green-900/10' : ''}
                    ${effectiveStatus === 'failed' || effectiveStatus === 'error' ? 'bg-red-900/10' : ''}
                  `}
                >
                  <div className="flex items-start gap-3">
                    {/* Step number and status */}
                    <div className="flex items-center gap-2 min-w-[4rem]">
                      <span className="text-gray-500 text-sm font-mono">{step.index + 1}.</span>
                      <span className={getStatusColor(effectiveStatus)}>
                        <StatusIcon status={effectiveStatus} />
                      </span>
                    </div>

                    {/* Step content */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm">
                        <span className={`font-semibold ${getKeywordColor(step.keyword)}`}>
                          {step.keyword}
                        </span>{' '}
                        <span className="text-gray-300">{step.text}</span>
                      </p>

                      {/* Duration */}
                      {result && (
                        <p className="text-xs text-gray-500 mt-1">
                          Duration: {formatDuration(result.duration_ms)}
                        </p>
                      )}

                      {/* Error message */}
                      {hasError && (
                        <div className="mt-2">
                          <button
                            onClick={() => setExpandedError(expandedError === step.index ? null : step.index)}
                            className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1"
                          >
                            <svg
                              className={`w-3 h-3 transition-transform ${expandedError === step.index ? 'rotate-90' : ''}`}
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 5l7 7-7 7"
                              />
                            </svg>
                            View error
                          </button>
                          {expandedError === step.index && (
                            <pre className="mt-2 p-2 bg-red-900/30 rounded text-xs text-red-300 overflow-x-auto">
                              {result.error_message}
                            </pre>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Re-run button for failed steps */}
                    {(effectiveStatus === 'failed' || effectiveStatus === 'error') && !isExecuting && (
                      <button
                        onClick={() => onExecuteStep(step.index)}
                        className="p-1 text-gray-400 hover:text-gray-200 transition-colors"
                        title="Retry this step"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                          />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Current step indicator */}
      {currentStepIndex < steps.length && !isExecuting && (
        <div className="p-3 bg-gray-800 border-t border-gray-700">
          <p className="text-xs text-gray-400 mb-1">Next step to execute:</p>
          <p className="text-sm text-gray-200 font-medium">
            {currentStepIndex + 1}. {steps[currentStepIndex]?.full}
          </p>
        </div>
      )}

      {/* All steps completed */}
      {currentStepIndex >= steps.length && steps.length > 0 && (
        <div className="p-4 bg-gray-800 border-t border-gray-700 text-center">
          <div
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg ${
              failedSteps > 0 ? 'bg-red-900/30 text-red-300' : 'bg-green-900/30 text-green-300'
            }`}
          >
            {failedSteps > 0 ? (
              <>
                <StatusIcon status="failed" />
                Test completed with {failedSteps} failure{failedSteps > 1 ? 's' : ''}
              </>
            ) : (
              <>
                <StatusIcon status="passed" />
                All steps passed!
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
