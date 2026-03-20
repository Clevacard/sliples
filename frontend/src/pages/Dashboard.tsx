import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { checkHealth, getTestRuns } from '../api/client'

interface HealthStatus {
  status: string
  database: string
  redis: string
}

interface TestRun {
  id: string
  status: string
  browser: string
  created_at: string
  finished_at?: string
}

export default function Dashboard() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [runs, setRuns] = useState<TestRun[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const [healthData, runsData] = await Promise.all([
          checkHealth(),
          getTestRuns({ limit: 10 }),
        ])
        setHealth(healthData)
        setRuns(runsData)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  const passedRuns = runs.filter((r) => r.status === 'passed').length
  const failedRuns = runs.filter((r) => r.status === 'failed').length
  const passRate = runs.length > 0 ? Math.round((passedRuns / runs.length) * 100) : 0

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      {/* Health Status */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">System Status</h3>
          <div className="flex items-center gap-2">
            <span
              className={`w-3 h-3 rounded-full ${
                health?.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'
              }`}
            />
            <span className="text-xl font-semibold capitalize">
              {health?.status || 'Unknown'}
            </span>
          </div>
        </div>

        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Database</h3>
          <div className="flex items-center gap-2">
            <span
              className={`w-3 h-3 rounded-full ${
                health?.database === 'connected' ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-xl font-semibold capitalize">
              {health?.database || 'Unknown'}
            </span>
          </div>
        </div>

        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Redis</h3>
          <div className="flex items-center gap-2">
            <span
              className={`w-3 h-3 rounded-full ${
                health?.redis === 'connected' ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-xl font-semibold capitalize">
              {health?.redis || 'Unknown'}
            </span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Runs</h3>
          <p className="text-3xl font-bold">{runs.length}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Passed</h3>
          <p className="text-3xl font-bold text-green-600">{passedRuns}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Failed</h3>
          <p className="text-3xl font-bold text-red-600">{failedRuns}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Pass Rate</h3>
          <p className="text-3xl font-bold text-primary-600">{passRate}%</p>
        </div>
      </div>

      {/* Recent Runs */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Recent Test Runs</h2>
          <Link to="/runs" className="text-primary-600 hover:text-primary-700 text-sm">
            View all
          </Link>
        </div>

        {runs.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No test runs yet. <Link to="/runs" className="text-primary-600">Create one</Link>
          </p>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-gray-500 border-b">
                <th className="pb-2">Status</th>
                <th className="pb-2">Browser</th>
                <th className="pb-2">Created</th>
                <th className="pb-2">Duration</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} className="border-b last:border-0">
                  <td className="py-3">
                    <Link to={`/runs/${run.id}`}>
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
                    </Link>
                  </td>
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
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
