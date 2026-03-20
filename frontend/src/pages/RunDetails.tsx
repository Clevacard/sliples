import { useEffect, useState, useCallback, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTestRunsStore, TestResult } from '../store/testRuns'
import Modal from '../components/Modal'

// Status icons
const StatusIcon = ({ status, size = 'sm' }: { status: string; size?: 'sm' | 'md' }) => {
  const sizeClass = size === 'md' ? 'w-5 h-5' : 'w-4 h-4'
  switch (status) {
    case 'passed':
      return (
        <svg className={sizeClass} fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      )
    case 'failed':
      return (
        <svg className={sizeClass} fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      )
    case 'running':
      return (
        <svg className={`${sizeClass} animate-spin`} fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )
    case 'skipped':
      return (
        <svg className={sizeClass} fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      )
    default:
      return (
        <svg className={sizeClass} fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
        </svg>
      )
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'passed': return 'text-green-400'
    case 'failed': return 'text-red-400'
    case 'running': return 'text-yellow-400'
    case 'skipped': return 'text-gray-400'
    default: return 'text-gray-400'
  }
}

const getStatusBgClass = (status: string) => {
  switch (status) {
    case 'passed': return 'bg-green-900/20 border-green-700/50'
    case 'failed': return 'bg-red-900/20 border-red-700/50'
    case 'running': return 'bg-yellow-900/20 border-yellow-700/50'
    case 'skipped': return 'bg-gray-800 border-gray-700'
    default: return 'bg-gray-800 border-gray-700'
  }
}

const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`
}

const AUTO_REFRESH_INTERVAL = 5000 // 5 seconds

export default function RunDetails() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { currentRun: run, loadingRun: loading, fetchRun, clearCurrentRun, environments, fetchEnvironments } = useTestRunsStore()

  const [selectedScreenshot, setSelectedScreenshot] = useState<string | null>(null)
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch run data
  const loadRun = useCallback(() => {
    if (id) fetchRun(id)
  }, [id, fetchRun])

  useEffect(() => {
    loadRun()
    fetchEnvironments()
    return () => clearCurrentRun()
  }, [loadRun, clearCurrentRun, fetchEnvironments])

  // Auto-refresh while running
  useEffect(() => {
    if (!run || run.status !== 'running' || !autoRefresh) return

    const interval = setInterval(() => {
      loadRun()
    }, AUTO_REFRESH_INTERVAL)

    return () => clearInterval(interval)
  }, [run?.status, autoRefresh, loadRun])

  // Calculate statistics
  const stats = useMemo(() => {
    if (!run?.results) return { passed: 0, failed: 0, skipped: 0, pending: 0, total: 0, progress: 0 }

    const passed = run.results.filter((r) => r.status === 'passed').length
    const failed = run.results.filter((r) => r.status === 'failed').length
    const skipped = run.results.filter((r) => r.status === 'skipped').length
    const pending = run.results.filter((r) => r.status === 'pending').length
    const total = run.results.length
    const completed = passed + failed + skipped
    const progress = total > 0 ? (completed / total) * 100 : 0

    return { passed, failed, skipped, pending, total, progress }
  }, [run?.results])

  const totalDuration = useMemo(() => {
    if (!run?.results) return 0
    return run.results.reduce((acc, r) => acc + (r.duration_ms || 0), 0)
  }, [run?.results])

  const toggleStep = (stepId: string) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev)
      if (next.has(stepId)) {
        next.delete(stepId)
      } else {
        next.add(stepId)
      }
      return next
    })
  }

  const getEnvName = (envId: string) => {
    return environments.find((e) => e.id === envId)?.name || envId
  }

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-48 bg-gray-700 rounded mb-8" />
        <div className="grid grid-cols-5 gap-4 mb-8">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-800 rounded-lg" />
          ))}
        </div>
        <div className="h-64 bg-gray-800 rounded-lg" />
      </div>
    )
  }

  if (!run) {
    return (
      <div className="text-center py-16">
        <svg
          className="w-16 h-16 mx-auto text-gray-600 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="text-gray-400 text-lg mb-2">Test run not found</p>
        <p className="text-gray-500 text-sm mb-6">
          The test run may have been deleted or does not exist
        </p>
        <button onClick={() => navigate('/runs')} className="btn btn-primary">
          Back to Test Runs
        </button>
      </div>
    )
  }

  return (
    <div>
      {/* Back Button */}
      <button
        onClick={() => navigate('/runs')}
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 mb-6 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Test Runs
      </button>

      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-100">Test Run Details</h1>
            <span className={`badge ${
              run.status === 'passed' ? 'badge-success' :
              run.status === 'failed' ? 'badge-error' :
              run.status === 'running' ? 'badge-warning' :
              'badge-info'
            }`}>
              <StatusIcon status={run.status} />
              {run.status}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-2 font-mono">ID: {run.id}</p>
          {run.triggered_by && (
            <p className="text-sm text-gray-400 mt-1">Triggered by: {run.triggered_by}</p>
          )}
        </div>
        <div className="flex gap-3">
          {run.status === 'running' && (
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`btn btn-sm ${autoRefresh ? 'btn-secondary' : 'btn-primary'}`}
            >
              {autoRefresh ? 'Pause Refresh' : 'Resume Refresh'}
            </button>
          )}
          <a
            href={`/api/v1/runs/${run.id}/report`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            View Report
          </a>
        </div>
      </div>

      {/* Progress Bar (for running tests) */}
      {run.status === 'running' && (
        <div className="card mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-400">Progress</span>
            <span className="text-sm text-gray-300">{Math.round(stats.progress)}%</span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-bar-fill bg-gradient-to-r from-blue-600 to-blue-400"
              style={{ width: `${stats.progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {stats.passed + stats.failed + stats.skipped} of {stats.total} steps completed
            {autoRefresh && ' - Auto-refreshing every 5s'}
          </p>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-700 rounded-lg">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Browser</p>
              <p className="text-gray-200 font-medium capitalize">
                {run.browser}
                {run.browser_version && <span className="text-gray-500 text-xs ml-1">v{run.browser_version}</span>}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-700 rounded-lg">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Duration</p>
              <p className="text-gray-200 font-medium">{formatDuration(totalDuration)}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-900/30 rounded-lg">
              <StatusIcon status="passed" size="md" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Passed</p>
              <p className="text-green-400 font-semibold text-lg">{stats.passed}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-900/30 rounded-lg">
              <StatusIcon status="failed" size="md" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Failed</p>
              <p className="text-red-400 font-semibold text-lg">{stats.failed}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-700 rounded-lg">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Environment</p>
              <p className="text-gray-200 font-medium">{getEnvName(run.environment_id || '')}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Test Steps */}
      <div className="card">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-100">Test Steps</h2>
          <div className="flex gap-2 text-sm">
            <span className="text-green-400">{stats.passed} passed</span>
            <span className="text-gray-600">|</span>
            <span className="text-red-400">{stats.failed} failed</span>
            {stats.skipped > 0 && (
              <>
                <span className="text-gray-600">|</span>
                <span className="text-gray-400">{stats.skipped} skipped</span>
              </>
            )}
          </div>
        </div>

        {run.results.length === 0 ? (
          <div className="text-center py-12">
            <svg
              className="w-12 h-12 mx-auto text-gray-600 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="text-gray-400">No test results yet</p>
            {run.status === 'running' && (
              <p className="text-gray-500 text-sm mt-2">Results will appear here as tests execute</p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {run.results.map((result: TestResult, index: number) => {
              const isExpanded = expandedSteps.has(result.id)
              const hasDetails = result.error_message || result.screenshot_url

              return (
                <div
                  key={result.id}
                  className={`rounded-lg border transition-all ${getStatusBgClass(result.status)}`}
                >
                  {/* Step Header */}
                  <div
                    className={`flex items-center justify-between p-4 ${hasDetails ? 'cursor-pointer' : ''}`}
                    onClick={() => hasDetails && toggleStep(result.id)}
                  >
                    <div className="flex items-center gap-4">
                      <span className="text-gray-500 font-mono text-sm w-8">{index + 1}.</span>
                      <span className={getStatusColor(result.status)}>
                        <StatusIcon status={result.status} />
                      </span>
                      <div>
                        <p className="text-gray-200 font-medium">{result.step_name}</p>
                        {result.scenario_name && (
                          <p className="text-gray-500 text-xs mt-0.5">{result.scenario_name}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-gray-500 text-sm">{formatDuration(result.duration_ms)}</span>
                      {result.screenshot_url && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedScreenshot(result.screenshot_url!)
                          }}
                          className="p-1.5 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                          title="View screenshot"
                        >
                          <svg className="w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        </button>
                      )}
                      {hasDetails && (
                        <svg
                          className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      )}
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && hasDetails && (
                    <div className="px-4 pb-4 ml-12 border-t border-gray-700/50 pt-4">
                      {result.error_message && (
                        <div className="mb-4">
                          <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Error Message</p>
                          <pre className="bg-gray-900 p-3 rounded-lg text-red-400 text-sm overflow-x-auto font-mono">
                            {result.error_message}
                          </pre>
                        </div>
                      )}
                      {result.screenshot_url && (
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Screenshot</p>
                          <button
                            onClick={() => setSelectedScreenshot(result.screenshot_url!)}
                            className="block"
                          >
                            <img
                              src={result.screenshot_url}
                              alt="Step screenshot"
                              className="max-w-xs rounded-lg border border-gray-700 hover:border-blue-500 transition-colors cursor-pointer"
                            />
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Screenshot Modal */}
      <Modal
        isOpen={!!selectedScreenshot}
        onClose={() => setSelectedScreenshot(null)}
        size="full"
        title="Screenshot"
      >
        {selectedScreenshot && (
          <div className="flex items-center justify-center">
            <img
              src={selectedScreenshot}
              alt="Screenshot"
              className="max-w-full max-h-[70vh] rounded-lg"
            />
          </div>
        )}
      </Modal>
    </div>
  )
}
