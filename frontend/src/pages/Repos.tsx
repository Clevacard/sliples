import { useEffect, useState } from 'react'
import { getRepos, createRepo, syncRepo, deleteRepo, getScenarios } from '../api/client'

interface Repo {
  id: string
  name: string
  git_url: string
  branch: string
  sync_path: string
  last_synced?: string
}

interface RepoWithCount extends Repo {
  scenario_count: number
}

interface Scenario {
  repo_id: string
}

// Confirmation Modal Component
function ConfirmModal({
  isOpen,
  title,
  message,
  confirmLabel,
  confirmVariant = 'danger',
  onConfirm,
  onCancel,
  isLoading,
}: {
  isOpen: boolean
  title: string
  message: string
  confirmLabel: string
  confirmVariant?: 'danger' | 'primary'
  onConfirm: () => void
  onCancel: () => void
  isLoading?: boolean
}) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md border border-gray-700 shadow-xl">
        <h2 className="text-xl font-semibold text-gray-100 mb-2">{title}</h2>
        <p className="text-gray-400 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={`btn ${confirmVariant === 'danger' ? 'btn-danger' : 'btn-primary'}`}
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Processing...
              </span>
            ) : (
              confirmLabel
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// Loading skeleton for repos
function ReposSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="card animate-pulse">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <div className="h-6 w-48 bg-gray-700 rounded mb-2" />
              <div className="h-4 w-72 bg-gray-700 rounded mb-3" />
              <div className="flex gap-4">
                <div className="h-3 w-24 bg-gray-700 rounded" />
                <div className="h-3 w-32 bg-gray-700 rounded" />
              </div>
            </div>
            <div className="flex gap-2">
              <div className="h-9 w-16 bg-gray-700 rounded" />
              <div className="h-9 w-20 bg-gray-700 rounded" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function Repos() {
  const [repos, setRepos] = useState<RepoWithCount[]>([])
  const [loading, setLoading] = useState(true)
  const [showNew, setShowNew] = useState(false)
  const [creating, setCreating] = useState(false)
  const [syncing, setSyncing] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<RepoWithCount | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Form state
  const [name, setName] = useState('')
  const [gitUrl, setGitUrl] = useState('')
  const [branch, setBranch] = useState('main')

  // Fetch repos and scenario counts
  async function fetchReposWithCounts() {
    try {
      const [reposData, scenariosData] = await Promise.all([
        getRepos(),
        getScenarios(),
      ])

      // Count scenarios per repo
      const reposWithCounts: RepoWithCount[] = reposData.map((repo: Repo) => ({
        ...repo,
        scenario_count: scenariosData.filter((s: Scenario) => s.repo_id === repo.id).length,
      }))

      setRepos(reposWithCounts)
    } catch (err) {
      console.error('Failed to fetch repos:', err)
      setError('Failed to load repositories')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReposWithCounts()
  }, [])

  // Auto-clear messages after 5 seconds
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [successMessage])

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [error])

  const handleCreate = async () => {
    if (!name.trim()) {
      setError('Repository name is required')
      return
    }
    if (!gitUrl.trim()) {
      setError('Git URL is required')
      return
    }

    // Basic URL validation
    if (!gitUrl.includes('git') && !gitUrl.includes('github') && !gitUrl.includes('gitlab')) {
      setError('Please enter a valid Git URL')
      return
    }

    setCreating(true)
    setError(null)
    try {
      const repo = await createRepo({ name: name.trim(), git_url: gitUrl.trim(), branch: branch.trim() || 'main' })
      setRepos([...repos, { ...repo, scenario_count: 0 }])
      setShowNew(false)
      setName('')
      setGitUrl('')
      setBranch('main')
      setSuccessMessage(`Repository "${repo.name}" added successfully`)
    } catch (err) {
      console.error('Failed to create repo:', err)
      setError('Failed to add repository. Please check the Git URL and try again.')
    } finally {
      setCreating(false)
    }
  }

  const handleSync = async (repo: RepoWithCount) => {
    setSyncing(repo.id)
    setError(null)
    try {
      await syncRepo(repo.id)
      setSuccessMessage(`Started syncing "${repo.name}"`)
      // Refresh repos after a short delay to get updated sync time
      setTimeout(() => fetchReposWithCounts(), 2000)
    } catch (err) {
      console.error('Failed to sync:', err)
      setError(`Failed to sync "${repo.name}"`)
    } finally {
      setSyncing(null)
    }
  }

  const handleDeleteConfirm = (repo: RepoWithCount) => {
    setDeleteConfirm(repo)
  }

  const handleDelete = async () => {
    if (!deleteConfirm) return

    setDeleting(deleteConfirm.id)
    setError(null)
    try {
      await deleteRepo(deleteConfirm.id)
      setRepos(repos.filter((r) => r.id !== deleteConfirm.id))
      setSuccessMessage(`Repository "${deleteConfirm.name}" deleted successfully`)
      setDeleteConfirm(null)
    } catch (err) {
      console.error('Failed to delete:', err)
      setError(`Failed to delete "${deleteConfirm.name}"`)
    } finally {
      setDeleting(null)
    }
  }

  const formatLastSynced = (date: string | undefined) => {
    if (!date) return 'Never synced'
    const d = new Date(date)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
    return d.toLocaleDateString()
  }

  return (
    <div className="p-8">
      {/* Success Message */}
      {successMessage && (
        <div className="mb-6 p-4 bg-green-500/20 border border-green-500/30 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-green-400">{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-green-400 hover:text-green-300">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span className="text-red-400">{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">Repositories</h1>
          <p className="text-gray-400 mt-1">Manage Git repositories containing test scenarios</p>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Repository
        </button>
      </div>

      {/* New Repo Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md border border-gray-700 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-100">Add Repository</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., my-tests"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoFocus
                />
                <p className="text-xs text-gray-500 mt-1">A friendly name for this repository</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Git URL <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="git@github.com:org/repo.git"
                  value={gitUrl}
                  onChange={(e) => setGitUrl(e.target.value)}
                />
                <p className="text-xs text-gray-500 mt-1">SSH or HTTPS URL to the Git repository</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Branch
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="main"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                />
                <p className="text-xs text-gray-500 mt-1">Branch to sync (defaults to main)</p>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-700">
              <button
                onClick={() => {
                  setShowNew(false)
                  setName('')
                  setGitUrl('')
                  setBranch('main')
                }}
                disabled={creating}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={creating || !name.trim() || !gitUrl.trim()}
                className="btn btn-primary"
              >
                {creating ? (
                  <span className="flex items-center gap-2">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Adding...
                  </span>
                ) : (
                  'Add Repository'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={deleteConfirm !== null}
        title="Delete Repository"
        message={`Are you sure you want to delete "${deleteConfirm?.name}"? This will also remove all associated scenarios. This action cannot be undone.`}
        confirmLabel="Delete"
        confirmVariant="danger"
        onConfirm={handleDelete}
        onCancel={() => setDeleteConfirm(null)}
        isLoading={deleting !== null}
      />

      {/* Repos List */}
      {loading ? (
        <ReposSkeleton />
      ) : repos.length === 0 ? (
        <div className="card text-center py-16">
          <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <h3 className="text-xl font-semibold text-gray-300 mb-2">No repositories configured</h3>
          <p className="text-gray-500 mb-6">
            Add a Git repository to import test scenarios.
          </p>
          <button
            onClick={() => setShowNew(true)}
            className="btn btn-primary inline-flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Your First Repository
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {repos.map((repo) => (
            <div key={repo.id} className="card hover:border-gray-600 transition-colors">
              <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-gray-700 rounded-lg">
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                      </svg>
                    </div>
                    <h3 className="font-semibold text-lg text-gray-100">{repo.name}</h3>
                    <span className="badge badge-info">{repo.scenario_count} scenarios</span>
                  </div>
                  <p className="text-sm text-gray-400 truncate mb-3">{repo.git_url}</p>
                  <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                      </svg>
                      {repo.branch}
                    </span>
                    <span className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {formatLastSynced(repo.last_synced)}
                    </span>
                    <span className="flex items-center gap-1 truncate">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                      </svg>
                      {repo.sync_path}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    onClick={() => handleSync(repo)}
                    disabled={syncing === repo.id}
                    className="btn btn-secondary btn-sm flex items-center gap-2"
                  >
                    {syncing === repo.id ? (
                      <>
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Syncing
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Sync
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => handleDeleteConfirm(repo)}
                    disabled={deleting === repo.id}
                    className="btn btn-secondary btn-sm text-red-400 hover:text-red-300 hover:bg-red-500/20"
                    title="Delete repository"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
