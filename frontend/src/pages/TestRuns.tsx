import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getTestRuns, getEnvironments, createTestRun } from '../api/client'

interface TestRun {
  id: string
  status: string
  browser: string
  environment_id: string
  created_at: string
  finished_at?: string
}

interface Environment {
  id: string
  name: string
}

export default function TestRuns() {
  const [runs, setRuns] = useState<TestRun[]>([])
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [loading, setLoading] = useState(true)
  const [showNewRun, setShowNewRun] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')

  // New run form
  const [newRunEnv, setNewRunEnv] = useState('')
  const [newRunTags, setNewRunTags] = useState('')
  const [newRunBrowsers, setNewRunBrowsers] = useState(['chrome'])
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    async function fetchData() {
      try {
        const [runsData, envsData] = await Promise.all([
          getTestRuns(statusFilter ? { status: statusFilter } : undefined),
          getEnvironments(),
        ])
        setRuns(runsData)
        setEnvironments(envsData)
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [statusFilter])

  const handleCreateRun = async () => {
    if (!newRunEnv) {
      alert('Please select an environment')
      return
    }

    setCreating(true)
    try {
      const run = await createTestRun({
        environment: newRunEnv,
        scenario_tags: newRunTags ? newRunTags.split(',').map((t) => t.trim()) : [],
        browsers: newRunBrowsers,
      })
      setRuns([run, ...runs])
      setShowNewRun(false)
      setNewRunEnv('')
      setNewRunTags('')
    } catch (error) {
      console.error('Failed to create run:', error)
      alert('Failed to create test run')
    } finally {
      setCreating(false)
    }
  }

  const getEnvName = (envId: string) => {
    return environments.find((e) => e.id === envId)?.name || envId
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Test Runs</h1>
        <button onClick={() => setShowNewRun(true)} className="btn btn-primary">
          New Test Run
        </button>
      </div>

      {/* New Run Modal */}
      {showNewRun && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">New Test Run</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Environment
                </label>
                <select
                  className="input"
                  value={newRunEnv}
                  onChange={(e) => setNewRunEnv(e.target.value)}
                >
                  <option value="">Select environment</option>
                  {environments.map((env) => (
                    <option key={env.id} value={env.name}>
                      {env.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="smoke, critical"
                  value={newRunTags}
                  onChange={(e) => setNewRunTags(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Browsers
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={newRunBrowsers.includes('chrome')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setNewRunBrowsers([...newRunBrowsers, 'chrome'])
                        } else {
                          setNewRunBrowsers(newRunBrowsers.filter((b) => b !== 'chrome'))
                        }
                      }}
                      className="mr-2"
                    />
                    Chrome
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={newRunBrowsers.includes('firefox')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setNewRunBrowsers([...newRunBrowsers, 'firefox'])
                        } else {
                          setNewRunBrowsers(newRunBrowsers.filter((b) => b !== 'firefox'))
                        }
                      }}
                      className="mr-2"
                    />
                    Firefox
                  </label>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowNewRun(false)} className="btn btn-secondary">
                Cancel
              </button>
              <button onClick={handleCreateRun} disabled={creating} className="btn btn-primary">
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex gap-4 items-center">
          <label className="text-sm font-medium text-gray-700">Filter by status:</label>
          <select
            className="input w-48"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="passed">Passed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Runs Table */}
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : runs.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">No test runs found.</p>
        </div>
      ) : (
        <div className="card">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-gray-500 border-b">
                <th className="pb-3">Status</th>
                <th className="pb-3">Environment</th>
                <th className="pb-3">Browser</th>
                <th className="pb-3">Created</th>
                <th className="pb-3">Duration</th>
                <th className="pb-3"></th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} className="border-b last:border-0">
                  <td className="py-3">
                    <span
                      className={`badge ${
                        run.status === 'passed'
                          ? 'badge-success'
                          : run.status === 'failed'
                          ? 'badge-error'
                          : run.status === 'running'
                          ? 'badge-info'
                          : 'badge-warning'
                      }`}
                    >
                      {run.status}
                    </span>
                  </td>
                  <td className="py-3">{getEnvName(run.environment_id)}</td>
                  <td className="py-3 capitalize">{run.browser}</td>
                  <td className="py-3 text-sm text-gray-600">
                    {new Date(run.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 text-sm text-gray-600">
                    {run.finished_at
                      ? `${Math.round(
                          (new Date(run.finished_at).getTime() -
                            new Date(run.created_at).getTime()) /
                            1000
                        )}s`
                      : '-'}
                  </td>
                  <td className="py-3">
                    <Link
                      to={`/runs/${run.id}`}
                      className="text-primary-600 hover:text-primary-700 text-sm"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
