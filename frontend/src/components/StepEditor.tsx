import { useState, useEffect, useMemo } from 'react'
import Editor from '@monaco-editor/react'
import type { CustomStep, CustomStepCreate, CustomStepUpdate } from '../api/client'

interface StepEditorProps {
  step?: CustomStep | null
  onSave: (data: CustomStepCreate | CustomStepUpdate) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

// Common step pattern examples
const PATTERN_EXAMPLES = [
  { pattern: 'I click on "{element}"', description: 'Click on an element by selector' },
  { pattern: 'I enter "{text}" into "{field}"', description: 'Type text into a field' },
  { pattern: 'I wait for {seconds} seconds', description: 'Wait for a duration' },
  { pattern: 'I should see "{text}"', description: 'Verify text is visible' },
  { pattern: 'the page title should be "{title}"', description: 'Check page title' },
  { pattern: 'I navigate to "{url}"', description: 'Navigate to a URL' },
  { pattern: 'I select "{option}" from "{dropdown}"', description: 'Select dropdown option' },
  { pattern: 'I hover over "{element}"', description: 'Hover over element' },
]

// Default Python implementation template
const DEFAULT_IMPLEMENTATION = `from playwright.sync_api import Page
from pytest_bdd import given, when, then

# Use @given, @when, or @then decorator based on your step type
@when('your pattern here')
def step_impl(page: Page):
    """
    Implement your step logic here.
    Available: page (Playwright Page object)
    """
    pass
`

export default function StepEditor({ step, onSave, onCancel, isLoading = false }: StepEditorProps) {
  const [name, setName] = useState(step?.name || '')
  const [pattern, setPattern] = useState(step?.pattern || '')
  const [description, setDescription] = useState(step?.description || '')
  const [implementation, setImplementation] = useState(step?.implementation || DEFAULT_IMPLEMENTATION)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [showExamples, setShowExamples] = useState(false)

  // Update form when step changes
  useEffect(() => {
    if (step) {
      setName(step.name)
      setPattern(step.pattern)
      setDescription(step.description || '')
      setImplementation(step.implementation)
    } else {
      setName('')
      setPattern('')
      setDescription('')
      setImplementation(DEFAULT_IMPLEMENTATION)
    }
    setErrors({})
  }, [step])

  // Generate Gherkin preview
  const gherkinPreview = useMemo(() => {
    if (!pattern) return null

    // Replace placeholders with example values for preview
    let preview = pattern
    preview = preview.replace(/"\{[^}]+\}"/g, '"example"')
    preview = preview.replace(/\{[^}]+\}/g, '5')

    return preview
  }, [pattern])

  // Validate form
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!pattern.trim()) {
      newErrors.pattern = 'Pattern is required'
    } else if (!pattern.includes('{') && !pattern.includes('"')) {
      // Pattern should typically have parameters, but this is just a warning
    }

    if (!implementation.trim()) {
      newErrors.implementation = 'Implementation is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) return

    const data: CustomStepCreate | CustomStepUpdate = {
      name: name.trim(),
      pattern: pattern.trim(),
      description: description.trim() || undefined,
      implementation: implementation,
    }

    await onSave(data)
  }

  const applyPatternExample = (examplePattern: string) => {
    setPattern(examplePattern)
    setShowExamples(false)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Step Name */}
      <div>
        <label htmlFor="step-name" className="block text-sm font-medium text-gray-300 mb-2">
          Step Name <span className="text-red-400">*</span>
        </label>
        <input
          id="step-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={`w-full px-4 py-2 bg-gray-700 border rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 ${
            errors.name ? 'border-red-500' : 'border-gray-600'
          }`}
          placeholder="e.g., Click Element Step"
          disabled={isLoading}
        />
        {errors.name && <p className="mt-1 text-sm text-red-400">{errors.name}</p>}
      </div>

      {/* Step Pattern */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label htmlFor="step-pattern" className="block text-sm font-medium text-gray-300">
            Step Pattern <span className="text-red-400">*</span>
          </label>
          <button
            type="button"
            onClick={() => setShowExamples(!showExamples)}
            className="text-xs text-primary-400 hover:text-primary-300"
          >
            {showExamples ? 'Hide Examples' : 'Show Examples'}
          </button>
        </div>
        <input
          id="step-pattern"
          type="text"
          value={pattern}
          onChange={(e) => setPattern(e.target.value)}
          className={`w-full px-4 py-2 bg-gray-700 border rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono ${
            errors.pattern ? 'border-red-500' : 'border-gray-600'
          }`}
          placeholder='e.g., I click on "{element}"'
          disabled={isLoading}
        />
        {errors.pattern && <p className="mt-1 text-sm text-red-400">{errors.pattern}</p>}
        <p className="mt-1 text-xs text-gray-500">
          Use {'{placeholder}'} for parameters. Wrap string params in quotes: {`"{param}"`}
        </p>

        {/* Pattern Examples */}
        {showExamples && (
          <div className="mt-3 p-3 bg-gray-900 rounded-lg border border-gray-700">
            <p className="text-xs font-medium text-gray-400 mb-2">Common Patterns:</p>
            <div className="space-y-2">
              {PATTERN_EXAMPLES.map((example, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => applyPatternExample(example.pattern)}
                  className="w-full text-left px-3 py-2 rounded bg-gray-800 hover:bg-gray-700 transition-colors"
                >
                  <span className="font-mono text-sm text-primary-400">{example.pattern}</span>
                  <span className="block text-xs text-gray-500 mt-0.5">{example.description}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Gherkin Preview */}
      {gherkinPreview && (
        <div className="p-3 bg-gray-900 rounded-lg border border-gray-700">
          <p className="text-xs font-medium text-gray-400 mb-2">Preview in Gherkin:</p>
          <div className="font-mono text-sm">
            <span className="text-purple-400">When</span>{' '}
            <span className="text-gray-300">{gherkinPreview}</span>
          </div>
        </div>
      )}

      {/* Description */}
      <div>
        <label htmlFor="step-description" className="block text-sm font-medium text-gray-300 mb-2">
          Description
        </label>
        <textarea
          id="step-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Brief description of what this step does..."
          rows={2}
          disabled={isLoading}
        />
      </div>

      {/* Python Implementation */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Python Implementation <span className="text-red-400">*</span>
        </label>
        <div className={`rounded-lg overflow-hidden border ${errors.implementation ? 'border-red-500' : 'border-gray-600'}`}>
          <Editor
            height="300px"
            defaultLanguage="python"
            value={implementation}
            onChange={(value) => setImplementation(value || '')}
            theme="vs-dark"
            options={{
              minimap: { enabled: false },
              fontSize: 13,
              lineNumbers: 'on',
              wordWrap: 'on',
              automaticLayout: true,
              scrollBeyondLastLine: false,
              tabSize: 4,
              insertSpaces: true,
              formatOnPaste: true,
              formatOnType: true,
            }}
          />
        </div>
        {errors.implementation && (
          <p className="mt-1 text-sm text-red-400">{errors.implementation}</p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          Write the pytest-bdd step definition. Use @given, @when, or @then decorators.
        </p>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-700">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          disabled={isLoading}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isLoading}
        >
          {isLoading ? 'Saving...' : step ? 'Update Step' : 'Create Step'}
        </button>
      </div>
    </form>
  )
}
