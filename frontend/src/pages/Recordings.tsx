import { useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useRecordingsStore } from '../store/recordings'
import { exportSessions } from '../api/client'
import StartRecordingModal from '../components/StartRecordingModal'

export default function Recordings() {
  const { sessions, isLoading, error, fetchSessions, deleteSession } = useRecordingsStore()

  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [deleting, setDeleting] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)
  const [showStartModal, setShowStartModal] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [exporting, setExporting] = useState(false)
  const [groupByDomain, setGroupByDomain] = useState(true)

  useEffect(() => {
    fetchSessions()
  }, [])

  const filteredSessions = useMemo(() => {
    return sessions.filter((session) => {
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        if (!session.name.toLowerCase().includes(query) && !session.url.toLowerCase().includes(query)) {
          return false
        }
      }
      if (statusFilter && session.status !== statusFilter) {
        return false
      }
      return true
    })
  }, [sessions, searchQuery, statusFilter])

  const handleDelete = async (sessionId: string) => {
    setDeleting(sessionId)
    try {
      await deleteSession(sessionId)
      setShowDeleteConfirm(null)
    } finally {
      setDeleting(null)
    }
  }

  const handleExport = async () => {
    if (selectedIds.size === 0) return
    setExporting(true)
    try {
      const data = await exportSessions(Array.from(selectedIds))
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `sessions-export-${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setExporting(false)
    }
  }

  const toggleSelection = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const groupedSessions = useMemo(() => {
    if (!groupByDomain) return { '': filteredSessions }
    const groups: Record<string, typeof filteredSessions> = {}
    for (const s of filteredSessions) {
      const key = s.domain || 'No domain'
      if (!groups[key]) groups[key] = []
      groups[key].push(s)
    }
    return groups
  }, [filteredSessions, groupByDomain])

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'recording':
        return 'badge-info'
      case 'stopped':
        return 'badge-success'
      case 'converted':
        return 'badge-warning'
      default:
        return 'badge'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-700 rounded w-40 animate-pulse" />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-700 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Recordings</h1>
          <p className="text-gray-400">Review and annotate UI recordings for conversion to test scenarios</p>
        </div>
        <div className="flex gap-2">
          {selectedIds.size > 0 && (
            <button
              onClick={handleExport}
              disabled={exporting}
              className="btn bg-purple-600 hover:bg-purple-700 text-white"
            >
              {exporting ? 'Exporting...' : `Export (${selectedIds.size})`}
            </button>
          )}
          <button
            onClick={() => setShowStartModal(true)}
            className="btn btn-primary"
          >
            + Start Recording
          </button>
        </div>
      </div>

      {/* Filter Card */}
      <div className="card">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[250px]">
            <label className="block text-sm font-medium text-gray-400 mb-2">Search</label>
            <input
              type="text"
              className="input w-full"
              placeholder="Search by name or URL..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="min-w-[150px]">
            <label className="block text-sm font-medium text-gray-400 mb-2">Status</label>
            <select
              className="input w-full"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="recording">Recording</option>
              <option value="stopped">Stopped</option>
              <option value="converted">Converted</option>
            </select>
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={groupByDomain}
                onChange={(e) => setGroupByDomain(e.target.checked)}
                className="rounded border-gray-600"
              />
              Group by domain
            </label>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="card bg-red-900/30 border border-red-700">
          <p className="text-red-200">{error}</p>
        </div>
      )}

      {/* Sessions Table */}
      {filteredSessions.length > 0 ? (
        <div className="space-y-4">
          {Object.entries(groupedSessions).map(([domain, domainSessions]) => (
            <div key={domain} className="card overflow-hidden">
              {groupByDomain && domain && (
                <div className="px-4 py-2 bg-gray-700/50 border-b border-gray-700">
                  <span className="text-sm font-medium text-gray-300">{domain}</span>
                  <span className="ml-2 text-xs text-gray-500">{domainSessions.length} session{domainSessions.length !== 1 ? 's' : ''}</span>
                </div>
              )}
              <table className="w-full table-dark">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="w-8 px-3 py-3"></th>
                    <th className="text-left px-4 py-3 text-gray-300 font-medium">Name</th>
                    <th className="text-left px-4 py-3 text-gray-300 font-medium">URL</th>
                    <th className="text-left px-4 py-3 text-gray-300 font-medium">Status</th>
                    <th className="text-left px-4 py-3 text-gray-300 font-medium">Events</th>
                    <th className="text-left px-4 py-3 text-gray-300 font-medium">Created</th>
                    <th className="text-right px-4 py-3 text-gray-300 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {domainSessions.map((session) => (
                    <tr key={session.id} className="border-b border-gray-700 hover:bg-gray-700/30">
                      <td className="px-3 py-3">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(session.id)}
                          onChange={() => toggleSelection(session.id)}
                          className="rounded border-gray-600"
                        />
                      </td>
                      <td className="px-4 py-3 text-gray-100">{session.name}</td>
                      <td className="px-4 py-3 text-gray-400 text-sm truncate max-w-xs">{session.url}</td>
                      <td className="px-4 py-3">
                        <span className={`badge ${getStatusBadgeClass(session.status)}`}>{session.status}</span>
                      </td>
                      <td className="px-4 py-3 text-gray-100">{session.event_count}</td>
                      <td className="px-4 py-3 text-gray-400 text-sm">{formatDate(session.created_at)}</td>
                      <td className="px-4 py-3 text-right space-x-2">
                        <Link
                          to={`/recordings/${session.id}`}
                          className="btn btn-sm bg-blue-600 hover:bg-blue-700 text-white"
                        >
                          View
                        </Link>
                        <button
                          onClick={() => setShowDeleteConfirm(session.id)}
                          className="btn btn-sm bg-red-600/30 hover:bg-red-600/50 text-red-300"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-400 mb-4">No recordings found</p>
          <p className="text-sm text-gray-500">
            {searchQuery || statusFilter ? 'Try adjusting your filters' : 'Use the recorder snippet to capture UI events'}
          </p>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-sm">
            <h3 className="text-lg font-semibold text-white mb-4">Delete Recording?</h3>
            <p className="text-gray-300 mb-6">This action cannot be undone.</p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="btn btn-secondary"
                disabled={deleting === showDeleteConfirm}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(showDeleteConfirm)}
                className="btn bg-red-600 hover:bg-red-700 text-white"
                disabled={deleting === showDeleteConfirm}
              >
                {deleting === showDeleteConfirm ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Start Recording Modal */}
      <StartRecordingModal
        isOpen={showStartModal}
        onClose={() => setShowStartModal(false)}
        onRecordingStarted={() => setShowStartModal(false)}
      />
    </div>
  )
}
