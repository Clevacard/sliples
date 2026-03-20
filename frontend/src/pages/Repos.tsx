import { useEffect, useState } from 'react'
import { getRepos, createRepo, syncRepo } from '../api/client'

interface Repo {
  id: string
  name: string
  git_url: string
  branch: string
  sync_path: string
  last_synced?: string
}

export default function Repos() {
  const [repos, setRepos] = useState<Repo[]>([])
  const [loading, setLoading] = useState(true)
  const [showNew, setShowNew] = useState(false)
  const [creating, setCreating] = useState(false)
  const [syncing, setSyncing] = useState<string | null>(null)

  // Form state
  const [name, setName] = useState('')
  const [gitUrl, setGitUrl] = useState('')
  const [branch, setBranch] = useState('main')

  useEffect(() => {
    async function fetchRepos() {
      try {
        const data = await getRepos()
        setRepos(data)
      } catch (error) {
        console.error('Failed to fetch repos:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchRepos()
  }, [])

  const handleCreate = async () => {
    if (!name || !gitUrl) {
      alert('Name and Git URL are required')
      return
    }

    setCreating(true)
    try {
      const repo = await createRepo({ name, git_url: gitUrl, branch })
      setRepos([...repos, repo])
      setShowNew(false)
      setName('')
      setGitUrl('')
      setBranch('main')
    } catch (error) {
      console.error('Failed to create repo:', error)
      alert('Failed to add repository')
    } finally {
      setCreating(false)
    }
  }

  const handleSync = async (id: string) => {
    setSyncing(id)
    try {
      await syncRepo(id)
      alert('Sync started')
    } catch (error) {
      console.error('Failed to sync:', error)
      alert('Failed to sync repository')
    } finally {
      setSyncing(null)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Repositories</h1>
        <button onClick={() => setShowNew(true)} className="btn btn-primary">
          Add Repository
        </button>
      </div>

      {/* New Repo Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">Add Repository</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., my-tests"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Git URL
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="git@github.com:org/repo.git"
                  value={gitUrl}
                  onChange={(e) => setGitUrl(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Branch
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="main"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowNew(false)} className="btn btn-secondary">
                Cancel
              </button>
              <button onClick={handleCreate} disabled={creating} className="btn btn-primary">
                {creating ? 'Adding...' : 'Add'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Repos List */}
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : repos.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 mb-4">No repositories configured.</p>
          <p className="text-sm text-gray-400">
            Add a git repository to import test scenarios.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {repos.map((repo) => (
            <div key={repo.id} className="card">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg">{repo.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{repo.git_url}</p>
                  <div className="flex gap-4 mt-2 text-xs text-gray-400">
                    <span>Branch: {repo.branch}</span>
                    <span>Path: {repo.sync_path}</span>
                    {repo.last_synced && (
                      <span>Last synced: {new Date(repo.last_synced).toLocaleString()}</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleSync(repo.id)}
                  disabled={syncing === repo.id}
                  className="btn btn-secondary"
                >
                  {syncing === repo.id ? 'Syncing...' : 'Sync'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
