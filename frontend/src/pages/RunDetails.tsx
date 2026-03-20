import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getTestRun } from '../api/client'

interface TestResult {
  id: string
  step_name: string
  status: string
  duration_ms: number
  error_message?: string
  screenshot_url?: string
}

interface TestRunDetail {
  id: string
  status: string
  browser: string
  browser_version: string
  triggered_by?: string
  started_at?: string
  finished_at?: string
  created_at: string
  results: TestResult[]
}

export default function RunDetails() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [run, setRun] = useState<TestRunDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedScreenshot, setSelectedScreenshot] = useState<string | null>(null)

  useEffect(() => {
    async function fetchRun() {
      if (!id) return
      try {
        const data = await getTestRun(id)
        setRun(data)
      } catch (error) {
        console.error('Failed to fetch run:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchRun()
  }, [id])

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  if (!run) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Test run not found.</p>
        <button onClick={() => navigate('/runs')} className="btn btn-primary mt-4">
          Back to Test Runs
        </button>
      </div>
    )
  }

  const passedSteps = run.results.filter((r) => r.status === 'passed').length
  const failedSteps = run.results.filter((r) => r.status === 'failed').length
  const totalDuration = run.results.reduce((acc, r) => acc + r.duration_ms, 0)

  return (
    <div>
      <button
        onClick={() => navigate('/runs')}
        className="text-sm text-gray-500 hover:text-gray-700 mb-4"
      >
        &larr; Back to Test Runs
      </button>

      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-2xl font-bold">Test Run Details</h1>
          <p className="text-sm text-gray-500 mt-1">ID: {run.id}</p>
        </div>
        <div className="flex gap-2">
          <a
            href={`/api/v1/runs/${run.id}/report`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
          >
            Download Report
          </a>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-5 gap-4 mb-8">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Status</h3>
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
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Browser</h3>
          <p className="capitalize">
            {run.browser} {run.browser_version}
          </p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Duration</h3>
          <p>{(totalDuration / 1000).toFixed(2)}s</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Passed</h3>
          <p className="text-green-600 font-semibold">{passedSteps}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Failed</h3>
          <p className="text-red-600 font-semibold">{failedSteps}</p>
        </div>
      </div>

      {/* Results */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Test Steps</h2>

        {run.results.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No results yet.</p>
        ) : (
          <div className="space-y-2">
            {run.results.map((result, index) => (
              <div
                key={result.id}
                className={`p-4 rounded-lg border ${
                  result.status === 'passed'
                    ? 'border-green-200 bg-green-50'
                    : result.status === 'failed'
                    ? 'border-red-200 bg-red-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-3">
                    <span className="text-gray-400 font-mono text-sm">{index + 1}</span>
                    <div>
                      <p className="font-medium">{result.step_name}</p>
                      {result.error_message && (
                        <p className="text-sm text-red-600 mt-1">{result.error_message}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-500">{result.duration_ms}ms</span>
                    <span
                      className={`badge ${
                        result.status === 'passed'
                          ? 'badge-success'
                          : result.status === 'failed'
                          ? 'badge-error'
                          : 'badge-warning'
                      }`}
                    >
                      {result.status}
                    </span>
                    {result.screenshot_url && (
                      <button
                        onClick={() => setSelectedScreenshot(result.screenshot_url!)}
                        className="text-primary-600 hover:text-primary-700 text-sm"
                      >
                        Screenshot
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Screenshot Modal */}
      {selectedScreenshot && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
          onClick={() => setSelectedScreenshot(null)}
        >
          <div className="max-w-4xl max-h-screen p-4">
            <img
              src={selectedScreenshot}
              alt="Screenshot"
              className="max-w-full max-h-full rounded-lg"
            />
          </div>
        </div>
      )}
    </div>
  )
}
