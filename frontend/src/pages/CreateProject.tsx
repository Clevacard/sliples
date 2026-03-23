import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectsStore } from '../store/projects'

export default function CreateProject() {
  const navigate = useNavigate()
  const { createProject, isLoading, error, clearError } = useProjectsStore()

  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [description, setDescription] = useState('')
  const [autoSlug, setAutoSlug] = useState(true)

  const generateSlug = (text: string) => {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 100)
  }

  const handleNameChange = (value: string) => {
    setName(value)
    if (autoSlug) {
      setSlug(generateSlug(value))
    }
  }

  const handleSlugChange = (value: string) => {
    setAutoSlug(false)
    setSlug(value.toLowerCase().replace(/[^a-z0-9-]/g, ''))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()

    try {
      const project = await createProject({
        name: name.trim(),
        slug: slug.trim() || undefined,
        description: description.trim() || undefined,
      })
      navigate(`/projects/${project.id}/settings`)
    } catch (err) {
      console.error('Failed to create project:', err)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
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
        <h1 className="text-2xl font-bold text-white">Create New Project</h1>
        <p className="text-gray-400 mt-1">
          Set up a new project to organize your test scenarios and environments
        </p>
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

      <form onSubmit={handleSubmit} className="card space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-2">
            Project Name *
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => handleNameChange(e.target.value)}
            className="input w-full"
            placeholder="My Awesome Project"
            required
            autoFocus
          />
        </div>

        <div>
          <label htmlFor="slug" className="block text-sm font-medium text-gray-300 mb-2">
            URL Slug
          </label>
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-sm">/projects/</span>
            <input
              type="text"
              id="slug"
              value={slug}
              onChange={(e) => handleSlugChange(e.target.value)}
              className="input flex-1"
              placeholder="my-awesome-project"
              pattern="^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$"
              title="Only lowercase letters, numbers, and hyphens. Cannot start/end with hyphen."
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Only lowercase letters, numbers, and hyphens. Auto-generated from name if left empty.
          </p>
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
            placeholder="Describe what this project is for..."
          />
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-300 mb-2">What's included</h3>
          <ul className="text-sm text-gray-400 space-y-1">
            <li className="flex items-center gap-2">
              <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Multiple environments (dev, staging, prod)
            </li>
            <li className="flex items-center gap-2">
              <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Scenario management with tags
            </li>
            <li className="flex items-center gap-2">
              <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Team collaboration with roles
            </li>
            <li className="flex items-center gap-2">
              <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Scheduled test runs
            </li>
          </ul>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-gray-700">
          <button
            type="button"
            onClick={() => navigate('/projects')}
            className="btn btn-secondary"
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isLoading || !name.trim()}
          >
            {isLoading ? (
              <>
                <svg className="w-4 h-4 animate-spin mr-2" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Creating...
              </>
            ) : (
              'Create Project'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
