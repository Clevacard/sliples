import { useEffect, useState } from 'react'
import { getEnvironments, createEnvironment } from '../api/client'

interface Environment {
  id: string
  name: string
  base_url: string
  credentials_env?: string
  variables: Record<string, string>
  retention_days: number
}

export default function Environments() {
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [loading, setLoading] = useState(true)
  const [showNew, setShowNew] = useState(false)
  const [creating, setCreating] = useState(false)

  // Form state
  const [name, setName] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [credentialsEnv, setCredentialsEnv] = useState('')

  useEffect(() => {
    async function fetchEnvironments() {
      try {
        const data = await getEnvironments()
        setEnvironments(data)
      } catch (error) {
        console.error('Failed to fetch environments:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchEnvironments()
  }, [])

  const handleCreate = async () => {
    if (!name || !baseUrl) {
      alert('Name and Base URL are required')
      return
    }

    setCreating(true)
    try {
      const env = await createEnvironment({
        name,
        base_url: baseUrl,
        variables: credentialsEnv ? { credentials_env: credentialsEnv } : {},
      })
      setEnvironments([...environments, env])
      setShowNew(false)
      setName('')
      setBaseUrl('')
      setCredentialsEnv('')
    } catch (error) {
      console.error('Failed to create environment:', error)
      alert('Failed to create environment')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Environments</h1>
        <button onClick={() => setShowNew(true)} className="btn btn-primary">
          Add Environment
        </button>
      </div>

      {/* New Environment Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">Add Environment</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., staging"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Base URL
                </label>
                <input
                  type="url"
                  className="input"
                  placeholder="https://staging.example.com"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Credentials Environment Variable
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="STAGING_CREDENTIALS"
                  value={credentialsEnv}
                  onChange={(e) => setCredentialsEnv(e.target.value)}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Environment variable name containing credentials
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowNew(false)} className="btn btn-secondary">
                Cancel
              </button>
              <button onClick={handleCreate} disabled={creating} className="btn btn-primary">
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Environments List */}
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : environments.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 mb-4">No environments configured.</p>
          <p className="text-sm text-gray-400">
            Add an environment to start running tests.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {environments.map((env) => (
            <div key={env.id} className="card">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg">{env.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{env.base_url}</p>
                  {env.credentials_env && (
                    <p className="text-xs text-gray-400 mt-1">
                      Credentials: {env.credentials_env}
                    </p>
                  )}
                </div>
                <div className="text-sm text-gray-500">
                  Retention: {env.retention_days} days
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
