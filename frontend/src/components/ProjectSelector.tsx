import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectsStore } from '../store/projects'

export default function ProjectSelector() {
  const navigate = useNavigate()
  const {
    projects,
    currentProject,
    isLoading,
    fetchProjects,
    setCurrentProject,
  } = useProjectsStore()

  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fetch projects on mount
  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSearchQuery('')
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const filteredProjects = projects.filter((project) =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.slug.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleSelectProject = (project: typeof projects[0]) => {
    setCurrentProject(project)
    setIsOpen(false)
    setSearchQuery('')
  }

  const handleCreateProject = () => {
    setIsOpen(false)
    setSearchQuery('')
    navigate('/projects/new')
  }

  const getRoleBadgeColor = (role?: string) => {
    switch (role) {
      case 'owner':
        return 'bg-purple-500/20 text-purple-400'
      case 'admin':
        return 'bg-blue-500/20 text-blue-400'
      case 'member':
        return 'bg-green-500/20 text-green-400'
      case 'viewer':
        return 'bg-gray-500/20 text-gray-400'
      default:
        return 'bg-gray-500/20 text-gray-400'
    }
  }

  if (isLoading && !currentProject) {
    return (
      <div className="flex items-center gap-2 text-gray-400">
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        Loading...
      </div>
    )
  }

  if (!currentProject && projects.length === 0) {
    return (
      <button
        onClick={handleCreateProject}
        className="btn btn-primary btn-sm flex items-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Create Project
      </button>
    )
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors min-w-[200px]"
      >
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
        <span className="flex-1 text-left truncate text-white">
          {currentProject?.name || 'Select Project'}
        </span>
        {currentProject?.current_user_role && (
          <span className={`text-xs px-1.5 py-0.5 rounded ${getRoleBadgeColor(currentProject.current_user_role)}`}>
            {currentProject.current_user_role}
          </span>
        )}
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute left-0 top-full mt-1 w-72 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50">
          {/* Search input */}
          <div className="p-2 border-b border-gray-700">
            <input
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-primary-500"
              autoFocus
            />
          </div>

          {/* Project list */}
          <div className="max-h-64 overflow-y-auto">
            {filteredProjects.length === 0 ? (
              <div className="p-4 text-sm text-gray-400 text-center">
                No projects found
              </div>
            ) : (
              filteredProjects.map((project) => (
                <button
                  key={project.id}
                  onClick={() => handleSelectProject(project)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-700 transition-colors ${
                    currentProject?.id === project.id ? 'bg-gray-700' : ''
                  }`}
                >
                  <svg className="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-white truncate">{project.name}</div>
                    <div className="text-xs text-gray-400 truncate">{project.slug}</div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {project.current_user_role && (
                      <span className={`text-xs px-1.5 py-0.5 rounded ${getRoleBadgeColor(project.current_user_role)}`}>
                        {project.current_user_role}
                      </span>
                    )}
                    {currentProject?.id === project.id && (
                      <svg className="w-4 h-4 text-primary-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Actions */}
          <div className="p-2 border-t border-gray-700">
            <button
              onClick={handleCreateProject}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-primary-400 hover:bg-gray-700 rounded transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create New Project
            </button>
            <button
              onClick={() => {
                setIsOpen(false)
                navigate('/projects')
              }}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-400 hover:bg-gray-700 rounded transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Manage Projects
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
