import { useState, useEffect } from 'react'
import { useSettingsStore } from '../store/settings'
import Modal, { ModalFooter } from './Modal'

export default function ApiKeyManager() {
  const {
    apiKeys,
    isLoadingKeys,
    isCreatingKey,
    isRevokingKey,
    keysError,
    fetchApiKeys,
    createApiKey,
    revokeApiKey,
    clearKeysError,
  } = useSettingsStore()

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isRevokeModalOpen, setIsRevokeModalOpen] = useState(false)
  const [keyToRevoke, setKeyToRevoke] = useState<{ id: string; name: string } | null>(null)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyValue, setNewKeyValue] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchApiKeys()
  }, [fetchApiKeys])

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) return

    try {
      const response = await createApiKey(newKeyName.trim())
      setNewKeyValue(response.key)
      setNewKeyName('')
    } catch {
      // Error is handled by store
    }
  }

  const handleCopyKey = async () => {
    if (newKeyValue) {
      await navigator.clipboard.writeText(newKeyValue)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleCloseCreateModal = () => {
    setIsCreateModalOpen(false)
    setNewKeyName('')
    setNewKeyValue(null)
    setCopied(false)
  }

  const handleOpenRevokeModal = (key: { id: string; name: string }) => {
    setKeyToRevoke(key)
    setIsRevokeModalOpen(true)
  }

  const handleConfirmRevoke = async () => {
    if (keyToRevoke) {
      try {
        await revokeApiKey(keyToRevoke.id)
        setIsRevokeModalOpen(false)
        setKeyToRevoke(null)
      } catch {
        // Error is handled by store
      }
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  if (isLoadingKeys) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-10 bg-gray-700 rounded w-32" />
        <div className="h-48 bg-gray-700 rounded" />
      </div>
    )
  }

  return (
    <div>
      {/* Error Alert */}
      {keysError && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg flex items-center justify-between">
          <span className="text-red-400 text-sm">{keysError}</span>
          <button onClick={clearKeysError} className="text-red-400 hover:text-red-300">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-medium text-gray-100">API Keys</h3>
          <p className="text-sm text-gray-400 mt-1">
            Manage API keys for CI/CD integration and programmatic access
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Key
        </button>
      </div>

      {/* Keys List */}
      {apiKeys.length === 0 ? (
        <div className="text-center py-12 bg-gray-800/50 rounded-lg border border-gray-700">
          <svg className="w-12 h-12 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
          <p className="text-gray-400 mb-2">No API keys yet</p>
          <p className="text-gray-500 text-sm">Create an API key to integrate with CI/CD pipelines</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="table-dark">
            <thead>
              <tr>
                <th>Name</th>
                <th>Key</th>
                <th>Created</th>
                <th>Last Used</th>
                <th className="w-20"></th>
              </tr>
            </thead>
            <tbody>
              {apiKeys.map((key) => (
                <tr key={key.id}>
                  <td className="font-medium text-gray-100">{key.name}</td>
                  <td>
                    <code className="text-sm bg-gray-700 px-2 py-1 rounded text-gray-300">
                      {key.key_prefix}...
                    </code>
                  </td>
                  <td className="text-sm text-gray-400">{formatDate(key.created_at)}</td>
                  <td className="text-sm text-gray-400">
                    {key.last_used_at ? formatDate(key.last_used_at) : 'Never'}
                  </td>
                  <td>
                    <button
                      onClick={() => handleOpenRevokeModal({ id: key.id, name: key.name })}
                      disabled={isRevokingKey === key.id}
                      className="text-red-400 hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                    >
                      {isRevokingKey === key.id ? 'Revoking...' : 'Revoke'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Key Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={handleCloseCreateModal}
        title={newKeyValue ? 'API Key Created' : 'Create API Key'}
        size="md"
      >
        {newKeyValue ? (
          <div className="space-y-4">
            <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <p className="text-yellow-500 font-medium text-sm">Copy your API key now</p>
                  <p className="text-yellow-500/70 text-xs mt-1">
                    This is the only time you will see the full key. Store it securely.
                  </p>
                </div>
              </div>
            </div>

            <div className="relative">
              <input
                type="text"
                value={newKeyValue}
                readOnly
                className="input w-full pr-24 font-mono text-sm"
              />
              <button
                onClick={handleCopyKey}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1 bg-gray-600 hover:bg-gray-500 text-gray-200 text-sm rounded transition-colors"
              >
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>

            <ModalFooter>
              <button onClick={handleCloseCreateModal} className="btn btn-primary">
                Done
              </button>
            </ModalFooter>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label htmlFor="keyName" className="block text-sm font-medium text-gray-300 mb-2">
                Key Name
              </label>
              <input
                id="keyName"
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., CI Pipeline, Jenkins, GitHub Actions"
                className="input w-full"
                autoFocus
              />
              <p className="text-xs text-gray-500 mt-2">
                Give your key a descriptive name to remember its purpose
              </p>
            </div>

            <ModalFooter>
              <button
                onClick={handleCloseCreateModal}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateKey}
                disabled={!newKeyName.trim() || isCreatingKey}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreatingKey ? 'Creating...' : 'Create Key'}
              </button>
            </ModalFooter>
          </div>
        )}
      </Modal>

      {/* Revoke Confirmation Modal */}
      <Modal
        isOpen={isRevokeModalOpen}
        onClose={() => setIsRevokeModalOpen(false)}
        title="Revoke API Key"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Are you sure you want to revoke the API key{' '}
            <span className="font-medium text-gray-100">"{keyToRevoke?.name}"</span>?
          </p>
          <p className="text-sm text-gray-400">
            This action cannot be undone. Any applications using this key will immediately lose access.
          </p>

          <ModalFooter>
            <button
              onClick={() => setIsRevokeModalOpen(false)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirmRevoke}
              disabled={!!isRevokingKey}
              className="btn bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
            >
              {isRevokingKey ? 'Revoking...' : 'Revoke Key'}
            </button>
          </ModalFooter>
        </div>
      </Modal>
    </div>
  )
}
