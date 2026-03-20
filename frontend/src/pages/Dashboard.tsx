import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useDashboardStore, TestRun } from '../store/dashboard'
import { checkHealth } from '../api/client'

interface HealthStatus {
  status: string
  database: string
  redis: string
}

// Simple SVG bar chart component
function TrendChart({ data }: { data: { date: string; passed: number; failed: number }[] }) {
  const maxValue = Math.max(
    ...data.map((d) => d.passed + d.failed),
    1 // Prevent division by zero
  )

  return (
    <div className="flex items-end gap-1 h-32">
      {data.map((day, i) => {
        const total = day.passed + day.failed
        const passedHeight = total > 0 ? (day.passed / maxValue) * 100 : 0
        const failedHeight = total > 0 ? (day.failed / maxValue) * 100 : 0
        const dayLabel = new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })

        return (
          <div key={day.date} className="flex-1 flex flex-col items-center gap-1">
            <div className="w-full flex flex-col-reverse h-24 rounded overflow-hidden bg-gray-700">
              {passedHeight > 0 && (
                <div
                  className="w-full bg-green-500 transition-all duration-300"
                  style={{ height: `${passedHeight}%` }}
                  title={`Passed: ${day.passed}`}
                />
              )}
              {failedHeight > 0 && (
                <div
                  className="w-full bg-red-500 transition-all duration-300"
                  style={{ height: `${failedHeight}%` }}
                  title={`Failed: ${day.failed}`}
                />
              )}
            </div>
            <span className="text-xs text-gray-500">{dayLabel}</span>
          </div>
        )
      })}
    </div>
  )
}

// Status badge component
function StatusBadge({ status }: { status: string }) {
  const badgeClass =
    status === 'passed'
      ? 'badge-success'
      : status === 'failed'
      ? 'badge-error'
      : status === 'running'
      ? 'badge-info'
      : status === 'pending'
      ? 'badge-pending'
      : 'badge-warning'

  return <span className={`badge ${badgeClass}`}>{status}</span>
}

// Stat card component
function StatCard({
  title,
  value,
  subtitle,
  valueColor,
  icon,
}: {
  title: string
  value: string | number
  subtitle?: string
  valueColor?: string
  icon?: React.ReactNode
}) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-2">{title}</h3>
          <p className={`text-3xl font-bold ${valueColor || 'text-gray-100'}`}>{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        {icon && <div className="text-gray-500">{icon}</div>}
      </div>
    </div>
  )
}

// Loading skeleton
function DashboardSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-8 w-48 bg-gray-700 rounded mb-8" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card">
            <div className="h-4 w-24 bg-gray-700 rounded mb-4" />
            <div className="h-6 w-16 bg-gray-700 rounded" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card">
            <div className="h-4 w-24 bg-gray-700 rounded mb-4" />
            <div className="h-8 w-20 bg-gray-700 rounded" />
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const {
    stats,
    recentRuns,
    isLoading,
    isRunningAllTests,
    isSyncingRepos,
    error,
    fetchDashboardData,
    runAllTests,
    syncAllRepositories,
    clearError,
  } = useDashboardStore()

  const [health, setHealth] = useState<HealthStatus | null>(null)

  useEffect(() => {
    fetchDashboardData()
    checkHealth()
      .then(setHealth)
      .catch((err) => console.error('Failed to fetch health:', err))
  }, [fetchDashboardData])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchDashboardData()
    }, 30000)
    return () => clearInterval(interval)
  }, [fetchDashboardData])

  const handleRunAllTests = () => {
    // Default to 'test' environment
    runAllTests('test')
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <DashboardSkeleton />
      </div>
    )
  }

  return (
    <div>
      {/* Error Alert */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-lg flex items-center justify-between">
          <span className="text-red-400">{error}</span>
          <button onClick={clearError} className="text-red-400 hover:text-red-300">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Header with Quick Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <h1 className="text-3xl font-bold text-gray-100">Dashboard</h1>
        <div className="flex gap-3">
          <button
            onClick={syncAllRepositories}
            disabled={isSyncingRepos}
            className="btn btn-secondary flex items-center gap-2"
          >
            {isSyncingRepos ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Syncing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Sync Repos
              </>
            )}
          </button>
          <button
            onClick={handleRunAllTests}
            disabled={isRunningAllTests}
            className="btn btn-primary flex items-center gap-2"
          >
            {isRunningAllTests ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Starting...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Run All Tests
              </>
            )}
          </button>
        </div>
      </div>

      {/* Health Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-2">System Status</h3>
          <div className="flex items-center gap-2">
            <span
              className={`w-3 h-3 rounded-full ${
                health?.status === 'healthy' ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'
              }`}
            />
            <span className="text-xl font-semibold capitalize text-gray-100">
              {health?.status || 'Unknown'}
            </span>
          </div>
        </div>

        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Database</h3>
          <div className="flex items-center gap-2">
            <span
              className={`w-3 h-3 rounded-full ${
                health?.database === 'connected' ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-xl font-semibold capitalize text-gray-100">
              {health?.database || 'Unknown'}
            </span>
          </div>
        </div>

        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Redis</h3>
          <div className="flex items-center gap-2">
            <span
              className={`w-3 h-3 rounded-full ${
                health?.redis === 'connected' ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-xl font-semibold capitalize text-gray-100">
              {health?.redis || 'Unknown'}
            </span>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Scenarios"
          value={stats?.totalScenarios ?? 0}
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
        />
        <StatCard
          title="Pass Rate"
          value={`${stats?.passRate ?? 0}%`}
          valueColor={
            (stats?.passRate ?? 0) >= 80
              ? 'text-green-400'
              : (stats?.passRate ?? 0) >= 50
              ? 'text-yellow-400'
              : 'text-red-400'
          }
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          title="Last 24h Runs"
          value={stats?.last24hRuns ?? 0}
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          title="Failed Tests"
          value={stats?.failedTests ?? 0}
          valueColor={stats?.failedTests ? 'text-red-400' : 'text-green-400'}
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />
      </div>

      {/* Trend Chart */}
      <div className="card mb-8">
        <h2 className="text-xl font-semibold text-gray-100 mb-4">Pass/Fail Trend (Last 7 Days)</h2>
        {stats?.trendData && stats.trendData.length > 0 ? (
          <>
            <TrendChart data={stats.trendData} />
            <div className="flex items-center justify-center gap-6 mt-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-green-500" />
                <span className="text-gray-400">Passed</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-red-500" />
                <span className="text-gray-400">Failed</span>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-8 text-gray-500">No trend data available yet</div>
        )}
      </div>

      {/* Recent Runs */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-100">Recent Test Runs</h2>
          <Link to="/runs" className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1">
            View all
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>

        {recentRuns.length === 0 ? (
          <div className="text-center py-12">
            <svg className="w-12 h-12 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="text-gray-500 mb-2">No test runs yet</p>
            <Link to="/runs" className="text-blue-400 hover:text-blue-300 text-sm">
              Create your first test run
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-dark">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Browser</th>
                  <th>Created</th>
                  <th>Duration</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {recentRuns.map((run: TestRun) => {
                  const duration = run.finished_at
                    ? Math.round(
                        (new Date(run.finished_at).getTime() - new Date(run.created_at).getTime()) / 1000
                      )
                    : null

                  return (
                    <tr key={run.id}>
                      <td>
                        <StatusBadge status={run.status} />
                      </td>
                      <td className="capitalize">{run.browser}</td>
                      <td className="text-sm text-gray-400">
                        {new Date(run.created_at).toLocaleString()}
                      </td>
                      <td className="text-sm">
                        {duration !== null ? (
                          <span className="text-gray-400">{duration}s</span>
                        ) : run.status === 'running' ? (
                          <span className="text-blue-400 flex items-center gap-1">
                            <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Running
                          </span>
                        ) : (
                          <span className="text-gray-600">-</span>
                        )}
                      </td>
                      <td>
                        <Link
                          to={`/runs/${run.id}`}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          Details
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
