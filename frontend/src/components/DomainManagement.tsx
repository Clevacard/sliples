import { useEffect, useState } from 'react'
import { AllowedDomain, IgnoredDomain, listDomains, addDomain, updateDomain, deleteDomain, getIgnoredDomains, dismissIgnoredDomain } from '../api/client'

interface Props {
  projectId: string
}

export default function DomainManagement({ projectId }: Props) {
  const [domains, setDomains] = useState<AllowedDomain[]>([])
  const [loading, setLoading] = useState(true)
  const [newDomain, setNewDomain] = useState('')
  const [adding, setAdding] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [ignoredDomains, setIgnoredDomains] = useState<IgnoredDomain[]>([])
  const [ignoredLoading, setIgnoredLoading] = useState(true)

  const load = async () => {
    try {
      const data = await listDomains(projectId)
      setDomains(data)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const loadIgnored = async () => {
    try {
      const data = await getIgnoredDomains()
      setIgnoredDomains(data)
    } catch {
      // non-critical
    } finally {
      setIgnoredLoading(false)
    }
  }

  useEffect(() => { load(); loadIgnored() }, [projectId])

  const handleAdd = async () => {
    if (!newDomain.trim()) return
    setAdding(true)
    setError(null)
    try {
      await addDomain(projectId, newDomain.trim())
      setNewDomain('')
      await load()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setAdding(false)
    }
  }

  const handleAddIgnored = async (domain: string) => {
    try {
      await addDomain(projectId, domain)
      await dismissIgnoredDomain(domain)
      await Promise.all([load(), loadIgnored()])
    } catch (e: any) {
      setError(e.message)
    }
  }

  const handleDismissIgnored = async (domain: string) => {
    try {
      await dismissIgnoredDomain(domain)
      await loadIgnored()
    } catch (e: any) {
      setError(e.message)
    }
  }

  const handleToggle = async (d: AllowedDomain) => {
    try {
      await updateDomain(projectId, d.id, { is_enabled: !d.is_enabled })
      await load()
    } catch (e: any) {
      setError(e.message)
    }
  }

  const handleSaveEdit = async (d: AllowedDomain) => {
    if (!editValue.trim()) return
    try {
      await updateDomain(projectId, d.id, { domain: editValue.trim() })
      setEditingId(null)
      await load()
    } catch (e: any) {
      setError(e.message)
    }
  }

  const handleDelete = async (d: AllowedDomain) => {
    try {
      await deleteDomain(projectId, d.id)
      await load()
    } catch (e: any) {
      setError(e.message)
    }
  }

  if (loading) {
    return <div className="animate-pulse h-20 bg-gray-700 rounded" />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Allowed Domains</h3>
          <p className="text-sm text-gray-400">Domains that can send recordings without an API key</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded p-3">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Add Domain */}
      <div className="flex gap-2">
        <input
          type="text"
          className="input flex-1"
          placeholder="example.com"
          value={newDomain}
          onChange={(e) => setNewDomain(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleAdd() }}
        />
        <button
          onClick={handleAdd}
          disabled={adding || !newDomain.trim()}
          className="btn btn-primary"
        >
          {adding ? 'Adding...' : 'Add Domain'}
        </button>
      </div>

      {/* Domain List */}
      {domains.length > 0 ? (
        <div className="space-y-2">
          {domains.map((d) => (
            <div key={d.id} className="flex items-center gap-3 bg-gray-700/30 rounded px-4 py-3">
              <button
                onClick={() => handleToggle(d)}
                className={`w-10 h-5 rounded-full relative transition-colors ${d.is_enabled ? 'bg-green-600' : 'bg-gray-600'}`}
              >
                <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${d.is_enabled ? 'left-5' : 'left-0.5'}`} />
              </button>

              {editingId === d.id ? (
                <div className="flex items-center gap-2 flex-1">
                  <input
                    type="text"
                    className="input flex-1 text-sm"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSaveEdit(d); if (e.key === 'Escape') setEditingId(null); }}
                    autoFocus
                  />
                  <button onClick={() => handleSaveEdit(d)} className="btn btn-sm btn-primary">Save</button>
                  <button onClick={() => setEditingId(null)} className="btn btn-sm btn-secondary">Cancel</button>
                </div>
              ) : (
                <>
                  <span
                    className={`flex-1 font-mono text-sm cursor-pointer hover:text-blue-300 ${d.is_enabled ? 'text-gray-200' : 'text-gray-500 line-through'}`}
                    onClick={() => { setEditingId(d.id); setEditValue(d.domain); }}
                  >
                    {d.domain}
                  </span>
                  <button
                    onClick={() => handleDelete(d)}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    Remove
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-500 text-sm">No domains configured. Add a domain to enable keyless recording.</p>
      )}

      {/* Ignored Domains */}
      {!ignoredLoading && ignoredDomains.length > 0 && (
        <div className="mt-8 space-y-3">
          <div>
            <h3 className="text-lg font-semibold text-yellow-300">Ignored Domains</h3>
            <p className="text-sm text-gray-400">Unregistered domains that attempted to send recordings</p>
          </div>
          <div className="space-y-2">
            {ignoredDomains.map((d) => (
              <div key={d.domain} className="flex items-center gap-3 bg-yellow-900/20 border border-yellow-800/30 rounded px-4 py-3">
                <span className="flex-1 font-mono text-sm text-yellow-200">{d.domain}</span>
                <span className="text-xs text-gray-400 tabular-nums">{d.count} req{d.count !== 1 ? 's' : ''}</span>
                <button
                  onClick={() => handleAddIgnored(d.domain)}
                  className="btn btn-sm btn-primary"
                >
                  Add
                </button>
                <button
                  onClick={() => handleDismissIgnored(d.domain)}
                  className="text-gray-400 hover:text-gray-200 text-sm"
                >
                  Dismiss
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
