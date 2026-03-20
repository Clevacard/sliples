import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Editor from '@monaco-editor/react'
import { getScenario } from '../api/client'

interface Scenario {
  id: string
  name: string
  feature_path: string
  content: string
  tags: string[]
}

export default function ScenarioEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [scenario, setScenario] = useState<Scenario | null>(null)
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    async function fetchScenario() {
      if (!id) return
      try {
        const data = await getScenario(id)
        setScenario(data)
        setContent(data.content || '')
      } catch (error) {
        console.error('Failed to fetch scenario:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchScenario()
  }, [id])

  const handleSave = async () => {
    setSaving(true)
    try {
      // TODO: Implement save API
      console.log('Saving:', content)
      await new Promise((resolve) => setTimeout(resolve, 500))
      alert('Saved successfully!')
    } catch (error) {
      console.error('Failed to save:', error)
      alert('Failed to save')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  if (!scenario) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Scenario not found.</p>
        <button onClick={() => navigate('/scenarios')} className="btn btn-primary mt-4">
          Back to Scenarios
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <button
            onClick={() => navigate('/scenarios')}
            className="text-sm text-gray-500 hover:text-gray-700 mb-2"
          >
            &larr; Back to Scenarios
          </button>
          <h1 className="text-2xl font-bold">{scenario.name}</h1>
          <p className="text-sm text-gray-500">{scenario.feature_path}</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn btn-primary"
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
      </div>

      <div className="flex gap-2 mb-4">
        {scenario.tags.map((tag) => (
          <span key={tag} className="badge badge-info">
            {tag}
          </span>
        ))}
      </div>

      <div className="card p-0 overflow-hidden" style={{ height: '600px' }}>
        <Editor
          height="100%"
          defaultLanguage="gherkin"
          value={content}
          onChange={(value) => setContent(value || '')}
          theme="vs-light"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            wordWrap: 'on',
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  )
}
