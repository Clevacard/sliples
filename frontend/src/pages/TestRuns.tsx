import { useEffect, useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTestRunsStore, TestRun } from '../store/testRuns'
import Modal, { ModalFooter } from '../components/Modal'
import { getScenarios } from '../api/client'

// Status icons as SVG components
const StatusIcon = ({ status }: { status: string }) => {
  switch (status) {
    case 'passed':
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      )
    case 'failed':
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      )
    case 'running':
      return (
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      )
    case 'queued':
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
        </svg>
      )
    default:
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      )
  }
}

const getStatusBadgeClass = (status: string) => {
  switch (status) {
    case 'passed':
      return 'badge-success'
    case 'failed':
      return 'badge-error'
    case 'running':
      return 'badge-warning'
    case 'queued':
      return 'badge-info'
    default:
      return 'badge-pending'
  }
}

const formatDuration = (start: string, end?: string) => {
  if (!end) return '-'
  const ms = new Date(end).getTime() - new Date(start).getTime()
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`
}

// Parse date as UTC (server returns UTC without Z suffix)
const parseDate = (date: string) => {
  // If no timezone indicator, treat as UTC
  if (!date.endsWith('Z') && !date.includes('+') && !date.includes('-', 10)) {
    return new Date(date + 'Z')
  }
  return new Date(date)
}

const formatDate = (date: string) => {
  const d = parseDate(date)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return d.toLocaleDateString()
}

interface Scenario {
  id: string
  name: string
  tags: string[]
}

export default function TestRuns() {
  const {
    runs,
    environments,
    browsers,
    loading,
    creating,
    error,
    filters,
    totalCount,
    fetchRuns,
    fetchEnvironments,
    fetchBrowsers,
    createRun,
    setFilters,
    resetFilters,
    clearError,
  } = useTestRunsStore()

  const navigate = useNavigate()
  const [showNewRunModal, setShowNewRunModal] = useState(false)
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loadingScenarios, setLoadingScenarios] = useState(false)

  // New run form state
  const [selectedEnvs, setSelectedEnvs] = useState<string[]>([])
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedBrowsers, setSelectedBrowsers] = useState<string[]>(['chromium'])
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  // Extract all unique tags from scenarios
  const allTags = useMemo(() => {
    const tags = new Set<string>()
    scenarios.forEach((s) => s.tags.forEach((t) => tags.add(t)))
    return Array.from(tags).sort()
  }, [scenarios])

  useEffect(() => {
    fetchRuns()
    fetchEnvironments()
    fetchBrowsers()
  }, [fetchRuns, fetchEnvironments, fetchBrowsers])

  useEffect(() => {
    if (showNewRunModal && scenarios.length === 0) {
      setLoadingScenarios(true)
      getScenarios()
        .then((data) => setScenarios(Array.isArray(data) ? data : data.items || []))
        .catch(console.error)
        .finally(() => setLoadingScenarios(false))
    }
  }, [showNewRunModal, scenarios.length])

  const handleApplyFilters = () => {
    setFilters({
      status: filters.status,
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
      page: 1,
    })
    fetchRuns()
  }

  const handleResetFilters = () => {
    setDateFrom('')
    setDateTo('')
    resetFilters()
    fetchRuns()
  }

  const handleCreateRun = async () => {
    if (selectedEnvs.length === 0 || selectedBrowsers.length === 0) {
      return
    }

    try {
      const createdRuns: TestRun[] = []

      // Create a run for each environment/browser combination
      for (const env of selectedEnvs) {
        for (const browser of selectedBrowsers) {
          const run = await createRun({
            environment: env,
            scenario_tags: selectedTags.length > 0 ? selectedTags : undefined,
            browsers: [browser],
          })
          createdRuns.push(run)
        }
      }

      setShowNewRunModal(false)
      setSelectedEnvs([])
      setSelectedTags([])
      setSelectedBrowsers(['chromium'])

      // If only one run, navigate to it; otherwise refresh the list
      if (createdRuns.length === 1) {
        navigate(`/runs/${createdRuns[0].id}`)
      } else {
        fetchRuns()
      }
    } catch (error) {
      console.error('Failed to create run:', error)
    }
  }

  const toggleEnv = (envName: string) => {
    setSelectedEnvs((prev) =>
      prev.includes(envName) ? prev.filter((e) => e !== envName) : [...prev, envName]
    )
  }

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    )
  }

  const toggleBrowser = (browser: string) => {
    setSelectedBrowsers((prev) =>
      prev.includes(browser) ? prev.filter((b) => b !== browser) : [...prev, browser]
    )
  }

  const totalPages = Math.ceil(totalCount / filters.limit)

  const getEnvName = (envId: string) => {
    return environments.find((e) => e.id === envId)?.name || envId
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">Test Runs</h1>
          <p className="text-gray-400 mt-1">Manage and monitor your test executions</p>
        </div>
        <button
          onClick={() => setShowNewRunModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Test Run
        </button>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Status</label>
            <select
              className="input w-40"
              value={filters.status || ''}
              onChange={(e) => setFilters({ status: e.target.value || undefined })}
            >
              <option value="">All statuses</option>
              <option value="queued">Queued</option>
              <option value="running">Running</option>
              <option value="passed">Passed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">From</label>
            <input
              type="date"
              className="input w-40"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">To</label>
            <input
              type="date"
              className="input w-40"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>

          <div className="flex gap-2">
            <button onClick={handleApplyFilters} className="btn btn-primary btn-sm">
              Apply
            </button>
            <button onClick={handleResetFilters} className="btn btn-secondary btn-sm">
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Runs Table */}
      {loading ? (
        <div className="card">
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex gap-4 animate-pulse">
                <div className="h-6 w-20 bg-gray-700 rounded" />
                <div className="h-6 w-32 bg-gray-700 rounded" />
                <div className="h-6 w-24 bg-gray-700 rounded" />
                <div className="h-6 flex-1 bg-gray-700 rounded" />
              </div>
            ))}
          </div>
        </div>
      ) : runs.length === 0 ? (
        <div className="card text-center py-16">
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
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <p className="text-gray-400 text-lg mb-2">No test runs found</p>
          <p className="text-gray-500 text-sm mb-6">
            Create a new test run to get started with testing
          </p>
          <button
            onClick={() => setShowNewRunModal(true)}
            className="btn btn-primary"
          >
            Create First Run
          </button>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="table-dark w-full">
            <thead>
              <tr className="bg-gray-900/50">
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Environment</th>
                <th className="px-6 py-4">Browser</th>
                <th className="px-6 py-4">Created</th>
                <th className="px-6 py-4">Duration</th>
                <th className="px-6 py-4">Results</th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run: TestRun) => (
                <tr key={run.id}>
                  <td className="px-6">
                    <span className={`badge ${getStatusBadgeClass(run.status)}`}>
                      <StatusIcon status={run.status} />
                      {run.status}
                    </span>
                  </td>
                  <td className="px-6">
                    <span className="text-gray-200">{run.environment_name || getEnvName(run.environment_id)}</span>
                  </td>
                  <td className="px-6">
                    <span className="capitalize text-gray-300">{run.browser}</span>
                    {run.browser_version && (
                      <span className="text-gray-500 text-xs ml-1">v{run.browser_version}</span>
                    )}
                  </td>
                  <td className="px-6">
                    <span className="text-gray-300" title={parseDate(run.created_at).toLocaleString()}>
                      {formatDate(run.created_at)}
                    </span>
                  </td>
                  <td className="px-6">
                    <span className="text-gray-300">
                      {formatDuration(run.created_at, run.finished_at)}
                    </span>
                  </td>
                  <td className="px-6">
                    {run.passed_count !== undefined && run.failed_count !== undefined ? (
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-green-400">{run.passed_count} passed</span>
                        <span className="text-gray-600">|</span>
                        <span className="text-red-400">{run.failed_count} failed</span>
                      </div>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-6">
                    <Link
                      to={`/runs/${run.id}`}
                      className="text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
                    >
                      View Details
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center mt-6">
          <p className="text-sm text-gray-400">
            Showing {(filters.page - 1) * filters.limit + 1} to{' '}
            {Math.min(filters.page * filters.limit, totalCount)} of {totalCount} runs
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => {
                setFilters({ page: filters.page - 1 })
                fetchRuns()
              }}
              disabled={filters.page === 1}
              className="btn btn-secondary btn-sm"
            >
              Previous
            </button>
            <span className="px-4 py-2 text-gray-400">
              Page {filters.page} of {totalPages}
            </span>
            <button
              onClick={() => {
                setFilters({ page: filters.page + 1 })
                fetchRuns()
              }}
              disabled={filters.page === totalPages}
              className="btn btn-secondary btn-sm"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* New Run Modal */}
      <Modal
        isOpen={showNewRunModal}
        onClose={() => {
          setShowNewRunModal(false)
          clearError()
        }}
        title="Create New Test Run"
        size="lg"
      >
        <div className="space-y-6">
          {/* Error message */}
          {error && (
            <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg flex items-start gap-3">
              <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="font-medium">Failed to create test run</p>
                <p className="text-sm text-red-300 mt-1">{error}</p>
              </div>
            </div>
          )}
          {/* Environment Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Environments <span className="text-red-400">*</span>
            </label>
            {environments.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {environments.map((env) => (
                  <label
                    key={env.id}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors ${
                      selectedEnvs.includes(env.name)
                        ? 'border-blue-500 bg-blue-900/30'
                        : 'border-gray-600 bg-gray-700/50 hover:border-gray-500'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedEnvs.includes(env.name)}
                      onChange={() => toggleEnv(env.name)}
                      className="rounded border-gray-500 bg-gray-700 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-gray-200">{env.name}</span>
                  </label>
                ))}
              </div>
            ) : (
              <p className="text-sm text-yellow-400">
                No environments available. Create one in the Environments page.
              </p>
            )}
            {selectedEnvs.length === 0 && environments.length > 0 && (
              <p className="text-sm text-yellow-400 mt-2">
                Please select at least one environment
              </p>
            )}
          </div>

          {/* Tags Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Filter Scenarios by Tags
            </label>
            {loadingScenarios ? (
              <div className="text-gray-400 text-sm">Loading tags...</div>
            ) : allTags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {allTags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => toggleTag(tag)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                      selectedTags.includes(tag)
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    @{tag}
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No tags available. Sync scenarios from repos.</p>
            )}
            {selectedTags.length > 0 && (
              <p className="text-sm text-gray-400 mt-2">
                Running scenarios with: {selectedTags.map((t) => `@${t}`).join(', ')}
              </p>
            )}
            {selectedTags.length === 0 && allTags.length > 0 && (
              <p className="text-sm text-gray-500 mt-2">
                No tags selected - all scenarios will run
              </p>
            )}
          </div>

          {/* Browser Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Browsers
            </label>
            <div className="flex gap-3">
              {(browsers.length > 0 ? browsers : [
                { id: 'chromium', name: 'Chromium' },
                { id: 'firefox', name: 'Firefox' },
                { id: 'webkit', name: 'WebKit' },
              ]).map((browser) => (
                <label
                  key={browser.id}
                  className={`flex items-center gap-2 px-4 py-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedBrowsers.includes(browser.id)
                      ? 'border-blue-500 bg-blue-900/30'
                      : 'border-gray-600 bg-gray-700/50 hover:border-gray-500'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedBrowsers.includes(browser.id)}
                    onChange={() => toggleBrowser(browser.id)}
                    className="rounded border-gray-500 bg-gray-700 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-200">{browser.name}</span>
                </label>
              ))}
            </div>
            {selectedBrowsers.length === 0 && (
              <p className="text-sm text-yellow-400 mt-2">
                Please select at least one browser
              </p>
            )}
          </div>

          {/* Summary */}
          {selectedEnvs.length > 0 && selectedBrowsers.length > 0 && (
            <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
              <p className="text-sm text-gray-300">
                <span className="text-blue-400 font-semibold">
                  {selectedEnvs.length * selectedBrowsers.length}
                </span>{' '}
                test run{selectedEnvs.length * selectedBrowsers.length > 1 ? 's' : ''} will be created:
              </p>
              <ul className="mt-2 text-xs text-gray-400 space-y-1">
                {selectedEnvs.map((env) =>
                  selectedBrowsers.map((browser) => (
                    <li key={`${env}-${browser}`}>
                      • {env} / {browser}
                    </li>
                  ))
                )}
              </ul>
            </div>
          )}
        </div>

        <ModalFooter>
          <button
            onClick={() => setShowNewRunModal(false)}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={handleCreateRun}
            disabled={creating || selectedEnvs.length === 0 || selectedBrowsers.length === 0}
            className="btn btn-primary flex items-center gap-2"
          >
            {creating ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Creating...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Start {selectedEnvs.length * selectedBrowsers.length > 1 ? `${selectedEnvs.length * selectedBrowsers.length} Runs` : 'Test Run'}
              </>
            )}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  )
}
