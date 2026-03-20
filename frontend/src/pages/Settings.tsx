import { useState, useEffect } from 'react'

export default function Settings() {
  const [apiKey, setApiKey] = useState('')
  const [savedKey, setSavedKey] = useState<string | null>(null)

  useEffect(() => {
    const key = localStorage.getItem('sliples_api_key')
    if (key) {
      setSavedKey(key.substring(0, 8) + '...')
    }
  }, [])

  const handleSaveKey = () => {
    if (!apiKey) {
      alert('Please enter an API key')
      return
    }
    localStorage.setItem('sliples_api_key', apiKey)
    setSavedKey(apiKey.substring(0, 8) + '...')
    setApiKey('')
    alert('API key saved')
  }

  const handleClearKey = () => {
    localStorage.removeItem('sliples_api_key')
    setSavedKey(null)
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      {/* API Key */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold mb-4">API Key</h2>
        <p className="text-sm text-gray-600 mb-4">
          Configure your API key for authenticating with the Sliples API.
          In development mode (no API keys in database), any key will work.
        </p>

        {savedKey ? (
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <p className="text-sm text-gray-500">Current key:</p>
              <p className="font-mono bg-gray-100 p-2 rounded">{savedKey}</p>
            </div>
            <button onClick={handleClearKey} className="btn btn-secondary">
              Clear
            </button>
          </div>
        ) : (
          <div className="flex gap-2">
            <input
              type="password"
              className="input flex-1"
              placeholder="Enter API key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
            <button onClick={handleSaveKey} className="btn btn-primary">
              Save
            </button>
          </div>
        )}
      </div>

      {/* About */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">About Sliples</h2>
        <div className="text-sm text-gray-600 space-y-2">
          <p>
            <strong>Version:</strong> 0.1.0
          </p>
          <p>
            <strong>Description:</strong> Web UI Automation Testing Platform
          </p>
          <p className="pt-2">
            Sliples allows you to write test scenarios in plain English (Gherkin),
            execute them across multiple browsers, and integrate with CI/CD pipelines.
          </p>
        </div>
      </div>

      {/* Documentation Links */}
      <div className="card mt-6">
        <h2 className="text-xl font-semibold mb-4">Documentation</h2>
        <div className="space-y-2">
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="block text-primary-600 hover:text-primary-700"
          >
            API Documentation (Swagger)
          </a>
          <a
            href="/api/v1/health"
            target="_blank"
            rel="noopener noreferrer"
            className="block text-primary-600 hover:text-primary-700"
          >
            Health Check Endpoint
          </a>
        </div>
      </div>
    </div>
  )
}
