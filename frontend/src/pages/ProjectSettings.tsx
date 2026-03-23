import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useProjectsStore } from '../store/projects'
import { ProjectRole } from '../api/client'
import Modal from '../components/Modal'

export default function ProjectSettings() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const {
    projects,
    currentProjectMembers,
    isLoading,
    isLoadingMembers,
    error,
    fetchProjects,
    fetchProjectMembers,
    updateProject,
    addMember,
    updateMemberRole,
    removeMember,
    clearError,
  } = useProjectsStore()

  const project = projects.find(p => p.id === id)

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Member management
  const [showAddMember, setShowAddMember] = useState(false)
  const [newMemberEmail, setNewMemberEmail] = useState('')
  const [newMemberRole, setNewMemberRole] = useState<ProjectRole>('member')
  const [isAddingMember, setIsAddingMember] = useState(false)
  const [removeMemberId, setRemoveMemberId] = useState<string | null>(null)
  const [isRemovingMember, setIsRemovingMember] = useState(false)

  useEffect(() => {
    if (!project) {
      fetchProjects()
    }
  }, [project, fetchProjects])

  useEffect(() => {
    if (id) {
      fetchProjectMembers(id)
    }
  }, [id, fetchProjectMembers])

  useEffect(() => {
    if (project) {
      setName(project.name)
      setDescription(project.description || '')
    }
  }, [project])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!id) return

    setIsSaving(true)
    setSaveSuccess(false)
    try {
      await updateProject(id, {
        name: name.trim(),
        description: description.trim() || undefined,
      })
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err) {
      console.error('Failed to update project:', err)
    } finally {
      setIsSaving(false)
    }
  }

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!id || !newMemberEmail.trim()) return

    setIsAddingMember(true)
    try {
      await addMember(id, newMemberEmail.trim(), newMemberRole)
      setShowAddMember(false)
      setNewMemberEmail('')
      setNewMemberRole('member')
    } catch (err) {
      console.error('Failed to add member:', err)
    } finally {
      setIsAddingMember(false)
    }
  }

  const handleRemoveMember = async () => {
    if (!id || !removeMemberId) return

    setIsRemovingMember(true)
    try {
      await removeMember(id, removeMemberId)
      setRemoveMemberId(null)
    } catch (err) {
      console.error('Failed to remove member:', err)
    } finally {
      setIsRemovingMember(false)
    }
  }

  const handleRoleChange = async (userId: string, newRole: ProjectRole) => {
    if (!id) return
    try {
      await updateMemberRole(id, userId, newRole)
    } catch (err) {
      console.error('Failed to update role:', err)
    }
  }

  const getRoleBadgeColor = (role: ProjectRole) => {
    switch (role) {
      case 'owner':
        return 'bg-purple-500/20 text-purple-400'
      case 'admin':
        return 'bg-blue-500/20 text-blue-400'
      case 'member':
        return 'bg-green-500/20 text-green-400'
      case 'viewer':
        return 'bg-gray-500/20 text-gray-400'
    }
  }

  const canManageMembers = project?.current_user_role === 'owner' || project?.current_user_role === 'admin'
  const isOwner = project?.current_user_role === 'owner'

  if (isLoading && !project) {
    return (
      <div className="p-6 flex items-center justify-center">
        <svg className="w-8 h-8 text-primary-500 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <h2 className="text-xl font-medium text-gray-300">Project not found</h2>
          <button onClick={() => navigate('/projects')} className="btn btn-primary mt-4">
            Back to Projects
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <button
          onClick={() => navigate('/projects')}
          className="text-gray-400 hover:text-white flex items-center gap-2 mb-4"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Projects
        </button>
        <h1 className="text-2xl font-bold text-white">Project Settings</h1>
        <p className="text-gray-400 mt-1">{project.slug}</p>
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

      <div className="grid gap-6 lg:grid-cols-2">
        {/* General Settings */}
        <div className="card">
          <h2 className="text-lg font-medium text-white mb-4">General</h2>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-2">
                Project Name
              </label>
              <input
                type="text"
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input w-full"
                required
              />
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="input w-full"
                rows={3}
              />
            </div>

            <div className="flex items-center gap-3">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSaving}
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
              {saveSuccess && (
                <span className="text-green-400 text-sm flex items-center gap-1">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Saved
                </span>
              )}
            </div>
          </form>
        </div>

        {/* Project Info */}
        <div className="card">
          <h2 className="text-lg font-medium text-white mb-4">Project Info</h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-400">Slug</dt>
              <dd className="text-gray-200 font-mono">{project.slug}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-400">Your Role</dt>
              <dd>
                <span className={`px-2 py-1 rounded text-xs ${getRoleBadgeColor(project.current_user_role!)}`}>
                  {project.current_user_role}
                </span>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-400">Members</dt>
              <dd className="text-gray-200">{project.member_count}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-400">Created</dt>
              <dd className="text-gray-200">{new Date(project.created_at).toLocaleDateString()}</dd>
            </div>
          </dl>
        </div>

        {/* Team Members */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-white">Team Members</h2>
            {canManageMembers && (
              <button
                onClick={() => setShowAddMember(true)}
                className="btn btn-sm btn-primary flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Member
              </button>
            )}
          </div>

          {isLoadingMembers ? (
            <div className="flex justify-center py-8">
              <svg className="w-6 h-6 text-primary-500 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-gray-400 border-b border-gray-700">
                    <th className="pb-3 font-medium">Member</th>
                    <th className="pb-3 font-medium">Role</th>
                    <th className="pb-3 font-medium">Joined</th>
                    {canManageMembers && <th className="pb-3 font-medium w-20">Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {currentProjectMembers.map((member) => (
                    <tr key={member.id} className="border-b border-gray-800">
                      <td className="py-3">
                        <div>
                          <div className="text-white">{member.name}</div>
                          <div className="text-sm text-gray-400">{member.email}</div>
                        </div>
                      </td>
                      <td className="py-3">
                        {canManageMembers && member.role !== 'owner' ? (
                          <select
                            value={member.role}
                            onChange={(e) => handleRoleChange(member.user_id, e.target.value as ProjectRole)}
                            className="input input-sm bg-gray-700 border-gray-600"
                            disabled={!isOwner && member.role === 'admin'}
                          >
                            <option value="viewer">Viewer</option>
                            <option value="member">Member</option>
                            {isOwner && <option value="admin">Admin</option>}
                          </select>
                        ) : (
                          <span className={`px-2 py-1 rounded text-xs ${getRoleBadgeColor(member.role)}`}>
                            {member.role}
                          </span>
                        )}
                      </td>
                      <td className="py-3 text-gray-400 text-sm">
                        {new Date(member.created_at).toLocaleDateString()}
                      </td>
                      {canManageMembers && (
                        <td className="py-3">
                          {member.role !== 'owner' && (isOwner || member.role !== 'admin') && (
                            <button
                              onClick={() => setRemoveMemberId(member.user_id)}
                              className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                              title="Remove member"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Add Member Modal */}
      <Modal
        isOpen={showAddMember}
        onClose={() => setShowAddMember(false)}
        title="Add Team Member"
      >
        <form onSubmit={handleAddMember} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={newMemberEmail}
              onChange={(e) => setNewMemberEmail(e.target.value)}
              className="input w-full"
              placeholder="user@example.com"
              required
              autoFocus
            />
            <p className="text-xs text-gray-500 mt-1">
              The user must already have an account in Sliples
            </p>
          </div>

          <div>
            <label htmlFor="role" className="block text-sm font-medium text-gray-300 mb-2">
              Role
            </label>
            <select
              id="role"
              value={newMemberRole}
              onChange={(e) => setNewMemberRole(e.target.value as ProjectRole)}
              className="input w-full"
            >
              <option value="viewer">Viewer - Can view only</option>
              <option value="member">Member - Can create and edit</option>
              {isOwner && <option value="admin">Admin - Can manage members</option>}
            </select>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              onClick={() => setShowAddMember(false)}
              className="btn btn-secondary"
              disabled={isAddingMember}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isAddingMember || !newMemberEmail.trim()}
            >
              {isAddingMember ? 'Adding...' : 'Add Member'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Remove Member Confirmation */}
      <Modal
        isOpen={!!removeMemberId}
        onClose={() => setRemoveMemberId(null)}
        title="Remove Member"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Are you sure you want to remove this member from the project? They will lose access to all project resources.
          </p>
          <div className="flex justify-end gap-3 mt-6">
            <button
              onClick={() => setRemoveMemberId(null)}
              className="btn btn-secondary"
              disabled={isRemovingMember}
            >
              Cancel
            </button>
            <button
              onClick={handleRemoveMember}
              className="btn bg-red-600 hover:bg-red-700 text-white"
              disabled={isRemovingMember}
            >
              {isRemovingMember ? 'Removing...' : 'Remove Member'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
