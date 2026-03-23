import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectsStore } from '../store/projects'
import Modal from '../components/Modal'
import { ProjectRole } from '../api/client'

export default function Projects() {
  const navigate = useNavigate()
  const {
    projects,
    currentProject,
    isLoading,
    error,
    fetchProjects,
    setCurrentProject,
    deleteProject,
    clearError,
  } = useProjectsStore()

  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const handleDelete = async () => {
    if (!deleteConfirmId) return
    setIsDeleting(true)
    try {
      await deleteProject(deleteConfirmId)
      setDeleteConfirmId(null)
    } catch (err) {
      console.error('Failed to delete project:', err)
    } finally {
      setIsDeleting(false)
    }
  }

  const getRoleBadgeColor = (role?: ProjectRole) => {
    switch (role) {
      case 'owner':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
      case 'admin':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      case 'member':
        return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'viewer':
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
  }

  const canDelete = (role?: ProjectRole) => role === 'owner'
  const canEdit = (role?: ProjectRole) => role === 'owner' || role === 'admin'

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Projects</h1>
          <p className="text-gray-400 mt-1">
            Manage your projects and team access
          </p>
        </div>
        <button
          onClick={() => navigate('/projects/new')}
          className="btn btn-primary flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Project
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-900/20 border border-red-700 rounded-lg text-red-400 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={clearError} className="text-red-400 hover:text-red-300">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <svg className="w-8 h-8 text-primary-500 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-12">
          <svg className="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-300 mb-2">No projects yet</h3>
          <p className="text-gray-400 mb-4">Create your first project to get started</p>
          <button
            onClick={() => navigate('/projects/new')}
            className="btn btn-primary"
          >
            Create Project
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <div
              key={project.id}
              className={`card hover:bg-gray-750 transition-colors cursor-pointer ${
                currentProject?.id === project.id ? 'ring-2 ring-primary-500' : ''
              }`}
              onClick={() => {
                setCurrentProject(project)
                navigate('/dashboard')
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary-500/20 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-medium text-white">{project.name}</h3>
                    <p className="text-xs text-gray-500">{project.slug}</p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded border ${getRoleBadgeColor(project.current_user_role)}`}>
                  {project.current_user_role}
                </span>
              </div>

              {project.description && (
                <p className="text-sm text-gray-400 mb-3 line-clamp-2">
                  {project.description}
                </p>
              )}

              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">
                  {project.member_count} member{project.member_count !== 1 ? 's' : ''}
                </span>
                <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                  {canEdit(project.current_user_role) && (
                    <button
                      onClick={() => navigate(`/projects/${project.id}/settings`)}
                      className="p-1 text-gray-400 hover:text-white transition-colors"
                      title="Settings"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    </button>
                  )}
                  {canDelete(project.current_user_role) && (
                    <button
                      onClick={() => setDeleteConfirmId(project.id)}
                      className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                      title="Delete"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>

              {currentProject?.id === project.id && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <span className="text-xs text-primary-400 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    Current Project
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteConfirmId}
        onClose={() => setDeleteConfirmId(null)}
        title="Delete Project"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Are you sure you want to delete this project? This action cannot be undone and will permanently delete:
          </p>
          <ul className="list-disc list-inside text-gray-400 text-sm space-y-1">
            <li>All environments</li>
            <li>All scenarios</li>
            <li>All test runs and reports</li>
            <li>All custom steps</li>
            <li>All schedules</li>
          </ul>
          <div className="flex justify-end gap-3 mt-6">
            <button
              onClick={() => setDeleteConfirmId(null)}
              className="btn btn-secondary"
              disabled={isDeleting}
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              className="btn bg-red-600 hover:bg-red-700 text-white"
              disabled={isDeleting}
            >
              {isDeleting ? 'Deleting...' : 'Delete Project'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
