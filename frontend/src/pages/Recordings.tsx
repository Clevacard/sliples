import { useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useRecordingsStore } from '../store/recordings'

export default function Recordings() {
  const { sessions, isLoading, error, fetchSessions, deleteSession } = useRecordingsStore()

  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [deleting, setDeleting] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)

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
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Recordings</h1>
        <p className="text-gray-400">Review and annotate UI recordings for conversion to test scenarios</p>
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
        <div className="card overflow-hidden">
          <table className="w-full table-dark">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left px-4 py-3 text-gray-300 font-medium">Name</th>
                <th className="text-left px-4 py-3 text-gray-300 font-medium">URL</th>
                <th className="text-left px-4 py-3 text-gray-300 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-gray-300 font-medium">Events</th>
                <th className="text-left px-4 py-3 text-gray-300 font-medium">Created</th>
                <th className="text-right px-4 py-3 text-gray-300 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredSessions.map((session) => (
                <tr key={session.id} className="border-b border-gray-700 hover:bg-gray-700/30">
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
    </div>
  )
}
