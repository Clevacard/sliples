import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getScenarios } from '../api/client'

interface Scenario {
  id: string
  name: string
  feature_path: string
  tags: string[]
  repo_id?: string
}

export default function Scenarios() {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loading, setLoading] = useState(true)
  const [tagFilter, setTagFilter] = useState('')

  useEffect(() => {
    async function fetchScenarios() {
      try {
        const data = await getScenarios(tagFilter ? { tag: tagFilter } : undefined)
        setScenarios(data)
      } catch (error) {
        console.error('Failed to fetch scenarios:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchScenarios()
  }, [tagFilter])

  const allTags = [...new Set(scenarios.flatMap((s) => s.tags))]

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Scenarios</h1>
        <button className="btn btn-primary">Sync All</button>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex gap-4 items-center">
          <label className="text-sm font-medium text-gray-700">Filter by tag:</label>
          <select
            className="input w-48"
            value={tagFilter}
            onChange={(e) => setTagFilter(e.target.value)}
          >
            <option value="">All tags</option>
            {allTags.map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : scenarios.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 mb-4">No scenarios found.</p>
          <p className="text-sm text-gray-400">
            Add a repository in <Link to="/repos" className="text-primary-600">Repos</Link> and sync to import scenarios.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {scenarios.map((scenario) => (
            <Link
              key={scenario.id}
              to={`/scenarios/${scenario.id}`}
              className="card hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg">{scenario.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{scenario.feature_path}</p>
                </div>
                <div className="flex gap-2">
                  {scenario.tags.map((tag) => (
                    <span key={tag} className="badge badge-info">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
