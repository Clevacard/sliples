import { useEffect, useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getScenarios, getRepos, createScenario, deleteScenario, syncScenarios } from '../api/client'
import { useProjectsStore } from '../store/projects'

interface Scenario {
  id: string
  name: string
  feature_path: string
  feature_name?: string
  tags: string[]
  repo_id?: string
  repo_name?: string
  description?: string
  step_count?: number
}

interface Repo {
  id: string
  name: string
  git_url: string
  branch?: string
}

// Convert name to a valid filename (lowercase, spaces to hyphens, remove special chars)
function toFilename(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
}

export default function Scenarios() {
  const navigate = useNavigate()
  const { currentProject } = useProjectsStore()
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [repos, setRepos] = useState<Repo[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newScenario, setNewScenario] = useState({
    name: '',
    filename: '',
    tags: '',
    content: `@smoke
Feature: New Feature
  As a user
  I want to test something
  So that I can verify it works

  Scenario: Test scenario
    Given I navigate to "https://example.com"
    Then I should see "Example"
`,
  })
  const [creating, setCreating] = useState(false)

  // Compute the base path for scenarios
  const scenarioBasePath = currentProject?.slug
    ? `scenarios/${currentProject.slug}/`
    : 'scenarios/'

  // Compute full feature path
  const featurePath = newScenario.filename
    ? `${scenarioBasePath}${newScenario.filename}${newScenario.filename.endsWith('.feature') ? '' : '.feature'}`
    : ''

  // Filters
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTag, setSelectedTag] = useState('')
  const [selectedRepo, setSelectedRepo] = useState('')

  // View mode
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list')

  useEffect(() => {
    async function fetchData() {
      try {
        const [scenariosData, reposData] = await Promise.all([
          getScenarios(),
          getRepos(),
        ])
        setScenarios(Array.isArray(scenariosData) ? scenariosData : scenariosData.items || [])
        setRepos(Array.isArray(reposData) ? reposData : reposData.items || [])
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  // Extract unique tags
  const allTags = useMemo(() => {
    const tags = new Set<string>()
    scenarios.forEach((s) => s.tags?.forEach((t) => tags.add(t)))
    return Array.from(tags).sort()
  }, [scenarios])

  // Filter scenarios
  const filteredScenarios = useMemo(() => {
    return scenarios.filter((scenario) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        const matchesName = scenario.name.toLowerCase().includes(query)
        const matchesPath = scenario.feature_path.toLowerCase().includes(query)
        const matchesTags = scenario.tags?.some((t) => t.toLowerCase().includes(query))
        if (!matchesName && !matchesPath && !matchesTags) return false
      }

      // Tag filter
      if (selectedTag && !scenario.tags?.includes(selectedTag)) return false

      // Repo filter
      if (selectedRepo && scenario.repo_id !== selectedRepo) return false

      return true
    })
  }, [scenarios, searchQuery, selectedTag, selectedRepo])

  // Group scenarios by feature file
  const groupedByFeature = useMemo(() => {
    const groups: Record<string, Scenario[]> = {}
    filteredScenarios.forEach((scenario) => {
      const key = scenario.feature_path || 'Unknown'
      if (!groups[key]) groups[key] = []
      groups[key].push(scenario)
    })
    return groups
  }, [filteredScenarios])

  const handleSyncAll = async () => {
    setSyncing('all')
    try {
      await syncScenarios()
      // Refresh scenarios after sync
      const data = await getScenarios()
      setScenarios(Array.isArray(data) ? data : data.items || [])
    } catch (error) {
      console.error('Failed to sync scenarios:', error)
      alert('Failed to sync scenarios from filesystem')
    } finally {
      setSyncing(null)
    }
  }

  const handleCreateScenario = async () => {
    if (!newScenario.name || !featurePath) return
    setCreating(true)
    try {
      const tags = newScenario.tags
        .split(',')
        .map((t) => t.trim().replace(/^@/, ''))
        .filter(Boolean)
      const created = await createScenario({
        name: newScenario.name,
        feature_path: featurePath,
        content: newScenario.content,
        tags,
      })
      setScenarios((prev) => [...prev, created])
      setShowCreateModal(false)
      setNewScenario({
        name: '',
        filename: '',
        tags: '',
        content: `@smoke
Feature: New Feature
  As a user
  I want to test something
  So that I can verify it works

  Scenario: Test scenario
    Given I navigate to "https://example.com"
    Then I should see "Example"
`,
      })
      // Navigate to the new scenario
      navigate(`/scenarios/${created.id}`)
    } catch (error) {
      console.error('Failed to create scenario:', error)
      alert('Failed to create scenario')
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteScenario = async (id: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm('Are you sure you want to delete this scenario?')) return
    setDeleting(id)
    try {
      await deleteScenario(id)
      setScenarios((prev) => prev.filter((s) => s.id !== id))
    } catch (error) {
      console.error('Failed to delete scenario:', error)
      alert('Failed to delete scenario')
    } finally {
      setDeleting(null)
    }
  }

  const getRepoName = (repoId?: string) => {
    if (!repoId) return 'Unknown'
    return repos.find((r) => r.id === repoId)?.name || repoId
  }

  const clearFilters = () => {
    setSearchQuery('')
    setSelectedTag('')
    setSelectedRepo('')
  }

  const hasActiveFilters = searchQuery || selectedTag || selectedRepo

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">Scenarios</h1>
          <p className="text-gray-400 mt-1">
            {scenarios.length} scenarios
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Scenario
          </button>
          <button
            onClick={handleSyncAll}
            disabled={syncing !== null}
            className="btn btn-secondary flex items-center gap-2"
          >
            <svg
              className={`w-5 h-5 ${syncing ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Sync from Disk
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-400 mb-2">Search</label>
            <div className="relative">
              <svg
                className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <input
                type="text"
                className="input pl-10"
                placeholder="Search scenarios by name, path, or tag..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          {/* Repository Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Repository</label>
            <select
              className="input w-48"
              value={selectedRepo}
              onChange={(e) => setSelectedRepo(e.target.value)}
            >
              <option value="">All repositories</option>
              {repos.map((repo) => (
                <option key={repo.id} value={repo.id}>
                  {repo.name}
                </option>
              ))}
            </select>
          </div>

          {/* Tag Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Tag</label>
            <select
              className="input w-40"
              value={selectedTag}
              onChange={(e) => setSelectedTag(e.target.value)}
            >
              <option value="">All tags</option>
              {allTags.map((tag) => (
                <option key={tag} value={tag}>
                  @{tag}
                </option>
              ))}
            </select>
          </div>

          {/* View Mode Toggle */}
          <div className="flex gap-1 bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-gray-600 text-white' : 'text-gray-400 hover:text-white'}`}
              title="List view"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-gray-600 text-white' : 'text-gray-400 hover:text-white'}`}
              title="Grid view"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
          </div>

          {hasActiveFilters && (
            <button onClick={clearFilters} className="btn btn-secondary btn-sm">
              Clear Filters
            </button>
          )}
        </div>

        {/* Active Filters Summary */}
        {hasActiveFilters && (
          <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-700">
            <span className="text-sm text-gray-500">Showing:</span>
            <span className="text-sm text-gray-300">
              {filteredScenarios.length} of {scenarios.length} scenarios
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="flex justify-between">
                <div className="space-y-3 flex-1">
                  <div className="h-5 w-3/4 bg-gray-700 rounded" />
                  <div className="h-4 w-1/2 bg-gray-700 rounded" />
                </div>
                <div className="flex gap-2">
                  <div className="h-6 w-16 bg-gray-700 rounded-full" />
                  <div className="h-6 w-16 bg-gray-700 rounded-full" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : scenarios.length === 0 ? (
        <div className="card text-center py-16">
          <svg
            className="w-16 h-16 mx-auto text-gray-600 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-gray-400 text-lg mb-2">No scenarios found</p>
          <p className="text-gray-500 text-sm mb-6">
            Add a repository in{' '}
            <Link to="/repos" className="text-blue-400 hover:text-blue-300">
              Repos
            </Link>{' '}
            and sync to import scenarios
          </p>
        </div>
      ) : filteredScenarios.length === 0 ? (
        <div className="card text-center py-12">
          <svg
            className="w-12 h-12 mx-auto text-gray-600 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <p className="text-gray-400 mb-2">No scenarios match your filters</p>
          <button onClick={clearFilters} className="text-blue-400 hover:text-blue-300 text-sm">
            Clear all filters
          </button>
        </div>
      ) : viewMode === 'grid' ? (
        // Grid View
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredScenarios.map((scenario) => (
            <Link
              key={scenario.id}
              to={`/scenarios/${scenario.id}`}
              className="card hover:border-blue-500/50 hover:shadow-lg transition-all group"
            >
              <div className="flex flex-col h-full">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-100 group-hover:text-blue-400 transition-colors mb-2">
                    {scenario.name}
                  </h3>
                  <p className="text-sm text-gray-500 font-mono truncate" title={scenario.feature_path}>
                    {scenario.feature_path}
                  </p>
                  {scenario.description && (
                    <p className="text-sm text-gray-400 mt-2 line-clamp-2">{scenario.description}</p>
                  )}
                </div>
                <div className="mt-4 pt-4 border-t border-gray-700 flex justify-between items-center">
                  <div className="flex flex-wrap gap-1.5">
                    {scenario.tags?.slice(0, 3).map((tag) => (
                      <span key={tag} className="badge badge-info text-xs">
                        @{tag}
                      </span>
                    ))}
                    {(scenario.tags?.length || 0) > 3 && (
                      <span className="badge badge-pending text-xs">
                        +{scenario.tags!.length - 3}
                      </span>
                    )}
                  </div>
                  {scenario.step_count && (
                    <span className="text-xs text-gray-500">{scenario.step_count} steps</span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        // List View - Grouped by Feature
        <div className="space-y-6">
          {Object.entries(groupedByFeature).map(([featurePath, featureScenarios]) => (
            <div key={featurePath} className="card p-0 overflow-hidden">
              {/* Feature Header */}
              <div className="px-6 py-4 bg-gray-900/50 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <svg
                      className="w-5 h-5 text-gray-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <span className="font-mono text-sm text-gray-300">{featurePath}</span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {featureScenarios.length} scenario{featureScenarios.length !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {/* Scenarios List */}
              <div className="divide-y divide-gray-700">
                {featureScenarios.map((scenario) => (
                  <Link
                    key={scenario.id}
                    to={`/scenarios/${scenario.id}`}
                    className="flex items-center justify-between px-6 py-4 hover:bg-gray-700/50 transition-colors group"
                  >
                    <div className="flex items-center gap-4">
                      <svg
                        className="w-5 h-5 text-gray-600 group-hover:text-blue-400 transition-colors"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M13 10V3L4 14h7v7l9-11h-7z"
                        />
                      </svg>
                      <div>
                        <h3 className="font-medium text-gray-200 group-hover:text-blue-400 transition-colors">
                          {scenario.name}
                        </h3>
                        {scenario.repo_name || scenario.repo_id ? (
                          <p className="text-xs text-gray-500 mt-0.5">
                            from {scenario.repo_name || getRepoName(scenario.repo_id)}
                          </p>
                        ) : null}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="flex flex-wrap gap-1.5 justify-end">
                        {scenario.tags?.map((tag) => (
                          <span key={tag} className="badge badge-info text-xs">
                            @{tag}
                          </span>
                        ))}
                      </div>
                      <button
                        onClick={(e) => handleDeleteScenario(scenario.id, e)}
                        disabled={deleting === scenario.id}
                        className="p-1.5 rounded hover:bg-red-900/50 text-gray-500 hover:text-red-400 transition-colors"
                        title="Delete scenario"
                      >
                        {deleting === scenario.id ? (
                          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                      <svg
                        className="w-5 h-5 text-gray-600 group-hover:text-gray-400 transition-colors"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Scenario Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-100">Create New Scenario</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Scenario Name *
                </label>
                <input
                  type="text"
                  className="input w-full"
                  placeholder="e.g., User Login"
                  value={newScenario.name}
                  onChange={(e) => {
                    const name = e.target.value
                    const filename = toFilename(name)
                    setNewScenario({ ...newScenario, name, filename })
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Feature Path *
                </label>
                <div className="flex items-center gap-0">
                  <span className="px-3 py-2 bg-gray-900 border border-r-0 border-gray-600 rounded-l-lg text-gray-400 text-sm">
                    {scenarioBasePath}
                  </span>
                  <input
                    type="text"
                    className="input flex-1 rounded-l-none"
                    placeholder="filename"
                    value={newScenario.filename}
                    onChange={(e) => setNewScenario({ ...newScenario, filename: e.target.value })}
                  />
                  <span className="px-3 py-2 bg-gray-900 border border-l-0 border-gray-600 rounded-r-lg text-gray-400 text-sm">
                    .feature
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Full path: {featurePath || '—'}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  className="input w-full"
                  placeholder="e.g., smoke, auth, critical"
                  value={newScenario.tags}
                  onChange={(e) => setNewScenario({ ...newScenario, tags: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Gherkin Content
                </label>
                <textarea
                  className="input w-full font-mono text-sm"
                  rows={12}
                  value={newScenario.content}
                  onChange={(e) => setNewScenario({ ...newScenario, content: e.target.value })}
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-700">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateScenario}
                disabled={creating || !newScenario.name || !newScenario.filename}
                className="btn btn-primary flex items-center gap-2"
              >
                {creating ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Creating...
                  </>
                ) : (
                  'Create Scenario'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
