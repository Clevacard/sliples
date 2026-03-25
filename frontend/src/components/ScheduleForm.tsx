import { useState, useEffect } from 'react'
import CronBuilder from './CronBuilder'
import { getEnvironments, getScenarios } from '../api/client'
import type { Schedule, ScheduleCreate, ScheduleUpdate, Environment } from '../api/client'

interface ScheduleFormProps {
  schedule?: Schedule | null
  onSubmit: (data: ScheduleCreate | ScheduleUpdate) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

interface ScenarioOption {
  id: string
  name: string
  tags: string[]
}

const AVAILABLE_BROWSERS = [
  { id: 'chromium', name: 'Chromium', icon: 'C' },
  { id: 'firefox', name: 'Firefox', icon: 'F' },
  { id: 'webkit', name: 'WebKit (Safari)', icon: 'W' },
]

export default function ScheduleForm({
  schedule,
  onSubmit,
  onCancel,
  isLoading = false,
}: ScheduleFormProps) {
  const [name, setName] = useState('')
  const [cronExpression, setCronExpression] = useState('0 9 * * *')
  const [timezone, setTimezone] = useState('UTC')
  const [environmentIds, setEnvironmentIds] = useState<string[]>([])
  const [browsers, setBrowsers] = useState<string[]>(['chromium'])
  const [scenarioTags, setScenarioTags] = useState<string[]>([])
  const [scenarioIds, setScenarioIds] = useState<string[]>([])
  const [enabled, setEnabled] = useState(true)
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Common timezones for schedule selection
  const COMMON_TIMEZONES = [
    { value: 'UTC', label: 'UTC' },
    { value: 'Europe/London', label: 'London (GMT/BST)' },
    { value: 'Europe/Paris', label: 'Paris (CET/CEST)' },
    { value: 'Europe/Berlin', label: 'Berlin (CET/CEST)' },
    { value: 'America/New_York', label: 'New York (EST/EDT)' },
    { value: 'America/Chicago', label: 'Chicago (CST/CDT)' },
    { value: 'America/Denver', label: 'Denver (MST/MDT)' },
    { value: 'America/Los_Angeles', label: 'Los Angeles (PST/PDT)' },
    { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
    { value: 'Asia/Shanghai', label: 'Shanghai (CST)' },
    { value: 'Asia/Singapore', label: 'Singapore (SGT)' },
    { value: 'Australia/Sydney', label: 'Sydney (AEST/AEDT)' },
  ]

  // Data for selects
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [scenarios, setScenarios] = useState<ScenarioOption[]>([])
  const [availableTags, setAvailableTags] = useState<string[]>([])
  const [loadingData, setLoadingData] = useState(true)

  // Selection mode
  const [selectionMode, setSelectionMode] = useState<'tags' | 'scenarios'>('tags')

  // Tag input
  const [tagInput, setTagInput] = useState('')

  const isEditing = !!schedule

  // Load environments and scenarios
  useEffect(() => {
    const loadData = async () => {
      try {
        const [envs, scenarioList] = await Promise.all([
          getEnvironments(),
          getScenarios(),
        ])
        setEnvironments(envs)
        setScenarios(scenarioList.map((s: { id: string; name: string; tags: string[] }) => ({
          id: s.id,
          name: s.name,
          tags: s.tags || [],
        })))

        // Collect all unique tags
        const tags = new Set<string>()
        scenarioList.forEach((s: { tags: string[] }) => {
          (s.tags || []).forEach((t: string) => tags.add(t))
        })
        setAvailableTags(Array.from(tags).sort())

        // Set default environment if none selected
        if (!schedule && envs.length > 0) {
          setEnvironmentIds([envs[0].id])
        }
      } catch (err) {
        console.error('Failed to load form data:', err)
      } finally {
        setLoadingData(false)
      }
    }
    loadData()
  }, [schedule])

  // Initialize form with schedule data
  useEffect(() => {
    if (schedule) {
      setName(schedule.name)
      setCronExpression(schedule.cron_expression)
      setTimezone(schedule.timezone || 'UTC')
      // Support both old single environment_id and new environment_ids array
      if (schedule.environment_ids && schedule.environment_ids.length > 0) {
        setEnvironmentIds(schedule.environment_ids)
      } else if (schedule.environment_id) {
        setEnvironmentIds([schedule.environment_id])
      }
      setBrowsers(schedule.browsers || ['chromium'])
      setScenarioTags(schedule.scenario_tags || [])
      setScenarioIds(schedule.scenario_ids || [])
      setEnabled(schedule.enabled)

      // Set selection mode based on what's configured
      if (schedule.scenario_ids && schedule.scenario_ids.length > 0) {
        setSelectionMode('scenarios')
      } else {
        setSelectionMode('tags')
      }
    } else {
      setName('')
      setCronExpression('0 9 * * *')
      setTimezone('UTC')
      setBrowsers(['chromium'])
      setScenarioTags([])
      setScenarioIds([])
      setEnabled(true)
      setSelectionMode('tags')
    }
    setErrors({})
  }, [schedule])

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!cronExpression.trim()) {
      newErrors.cronExpression = 'Cron expression is required'
    } else if (cronExpression.split(' ').length !== 5) {
      newErrors.cronExpression = 'Invalid cron expression format'
    }

    if (environmentIds.length === 0) {
      newErrors.environmentIds = 'Select at least one environment'
    }

    if (browsers.length === 0) {
      newErrors.browsers = 'Select at least one browser'
    }

    if (selectionMode === 'tags' && scenarioTags.length === 0) {
      newErrors.selection = 'Select at least one tag'
    }

    if (selectionMode === 'scenarios' && scenarioIds.length === 0) {
      newErrors.selection = 'Select at least one scenario'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    const data: ScheduleCreate | ScheduleUpdate = {
      name: name.trim(),
      cron_expression: cronExpression,
      timezone,
      environment_ids: environmentIds,
      browsers,
      scenario_tags: selectionMode === 'tags' ? scenarioTags : [],
      scenario_ids: selectionMode === 'scenarios' ? scenarioIds : [],
      enabled,
    }

    await onSubmit(data)
  }

  const toggleBrowser = (browserId: string) => {
    setBrowsers((prev) =>
      prev.includes(browserId)
        ? prev.filter((b) => b !== browserId)
        : [...prev, browserId]
    )
  }

  const toggleEnv = (envId: string) => {
    setEnvironmentIds((prev) =>
      prev.includes(envId)
        ? prev.filter((id) => id !== envId)
        : [...prev, envId]
    )
  }

  const addTag = (tag: string) => {
    const trimmed = tag.trim()
    if (trimmed && !scenarioTags.includes(trimmed)) {
      setScenarioTags([...scenarioTags, trimmed])
    }
    setTagInput('')
  }

  const removeTag = (tag: string) => {
    setScenarioTags(scenarioTags.filter((t) => t !== tag))
  }

  const toggleScenario = (scenarioId: string) => {
    setScenarioIds((prev) =>
      prev.includes(scenarioId)
        ? prev.filter((id) => id !== scenarioId)
        : [...prev, scenarioId]
    )
  }

  if (loadingData) {
    return (
      <div className="flex items-center justify-center py-8">
        <svg className="animate-spin h-6 w-6 text-primary-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Name */}
      <div>
        <label htmlFor="schedule-name" className="block text-sm font-medium text-gray-300 mb-1">
          Schedule Name <span className="text-red-400">*</span>
        </label>
        <input
          id="schedule-name"
          type="text"
          className={`w-full px-3 py-2 bg-gray-700 border rounded-lg text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
            errors.name ? 'border-red-500' : 'border-gray-600'
          }`}
          placeholder="e.g., Nightly Regression Tests"
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={isLoading}
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-400">{errors.name}</p>
        )}
      </div>

      {/* Cron Expression */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Schedule <span className="text-red-400">*</span>
        </label>
        <CronBuilder
          value={cronExpression}
          onChange={setCronExpression}
          disabled={isLoading}
        />
        {errors.cronExpression && (
          <p className="mt-1 text-sm text-red-400">{errors.cronExpression}</p>
        )}
      </div>

      {/* Timezone */}
      <div>
        <label htmlFor="schedule-timezone" className="block text-sm font-medium text-gray-300 mb-1">
          Timezone
        </label>
        <select
          id="schedule-timezone"
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          disabled={isLoading}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          {COMMON_TIMEZONES.map((tz) => (
            <option key={tz.value} value={tz.value}>
              {tz.label}
            </option>
          ))}
        </select>
        <p className="mt-1 text-xs text-gray-400">
          The cron schedule will be evaluated in this timezone
        </p>
      </div>

      {/* Environments */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Environments <span className="text-red-400">*</span>
        </label>
        <div className="grid grid-cols-2 gap-2">
          {environments.map((env) => (
            <label
              key={env.id}
              className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-colors ${
                environmentIds.includes(env.id)
                  ? 'border-primary-500 bg-primary-500/10'
                  : 'border-gray-600 bg-gray-700 hover:border-gray-500'
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <input
                type="checkbox"
                checked={environmentIds.includes(env.id)}
                onChange={() => toggleEnv(env.id)}
                disabled={isLoading}
                className="w-4 h-4 rounded border-gray-500 bg-gray-600 text-primary-500 focus:ring-primary-500"
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-200 truncate">{env.name}</p>
                <p className="text-xs text-gray-400 truncate">{env.base_url}</p>
              </div>
            </label>
          ))}
        </div>
        {errors.environmentIds && (
          <p className="mt-1 text-sm text-red-400">{errors.environmentIds}</p>
        )}
      </div>

      {/* Browsers */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Browsers <span className="text-red-400">*</span>
        </label>
        <div className="flex gap-2">
          {AVAILABLE_BROWSERS.map((browser) => (
            <button
              key={browser.id}
              type="button"
              onClick={() => toggleBrowser(browser.id)}
              disabled={isLoading}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
                browsers.includes(browser.id)
                  ? 'border-primary-500 bg-primary-500/10 text-primary-300'
                  : 'border-gray-600 bg-gray-700 text-gray-300 hover:border-gray-500'
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span className="w-6 h-6 rounded bg-gray-600 flex items-center justify-center text-xs font-bold">
                {browser.icon}
              </span>
              <span className="text-sm">{browser.name}</span>
            </button>
          ))}
        </div>
        {errors.browsers && (
          <p className="mt-1 text-sm text-red-400">{errors.browsers}</p>
        )}
      </div>

      {/* Scenario Selection Mode */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Run Scenarios <span className="text-red-400">*</span>
        </label>
        <div className="flex gap-2 mb-3">
          <button
            type="button"
            onClick={() => setSelectionMode('tags')}
            disabled={isLoading}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              selectionMode === 'tags'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            By Tags
          </button>
          <button
            type="button"
            onClick={() => setSelectionMode('scenarios')}
            disabled={isLoading}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              selectionMode === 'scenarios'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            Individual Scenarios
          </button>
        </div>

        {/* Tags Selection */}
        {selectionMode === 'tags' && (
          <div className="space-y-2">
            <div className="flex gap-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addTag(tagInput)
                  }
                }}
                placeholder="Type a tag and press Enter"
                className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isLoading}
              />
            </div>
            {availableTags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {availableTags.filter((t) => !scenarioTags.includes(t)).slice(0, 10).map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => addTag(tag)}
                    disabled={isLoading}
                    className="px-2 py-0.5 text-xs bg-gray-700 text-gray-400 rounded hover:bg-gray-600 hover:text-gray-200"
                  >
                    + {tag}
                  </button>
                ))}
              </div>
            )}
            {scenarioTags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {scenarioTags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-primary-500/20 text-primary-300 rounded-lg text-sm"
                  >
                    @{tag}
                    <button
                      type="button"
                      onClick={() => removeTag(tag)}
                      disabled={isLoading}
                      className="hover:text-red-400"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Individual Scenarios Selection */}
        {selectionMode === 'scenarios' && (
          <div className="max-h-48 overflow-y-auto border border-gray-600 rounded-lg bg-gray-700/50">
            {scenarios.length === 0 ? (
              <p className="p-3 text-sm text-gray-400">No scenarios available</p>
            ) : (
              <div className="divide-y divide-gray-600">
                {scenarios.map((scenario) => (
                  <label
                    key={scenario.id}
                    className={`flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-gray-700/50 ${
                      scenarioIds.includes(scenario.id) ? 'bg-primary-500/10' : ''
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={scenarioIds.includes(scenario.id)}
                      onChange={() => toggleScenario(scenario.id)}
                      disabled={isLoading}
                      className="w-4 h-4 rounded border-gray-500 bg-gray-600 text-primary-500 focus:ring-primary-500 focus:ring-offset-gray-800"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-200 truncate">{scenario.name}</p>
                      {scenario.tags.length > 0 && (
                        <p className="text-xs text-gray-500 truncate">
                          {scenario.tags.map((t) => `@${t}`).join(' ')}
                        </p>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>
        )}

        {errors.selection && (
          <p className="mt-1 text-sm text-red-400">{errors.selection}</p>
        )}
      </div>

      {/* Enabled Toggle */}
      <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
        <div>
          <p className="text-sm font-medium text-gray-200">Enabled</p>
          <p className="text-xs text-gray-400">Schedule will run automatically when enabled</p>
        </div>
        <button
          type="button"
          onClick={() => setEnabled(!enabled)}
          disabled={isLoading}
          className={`relative w-11 h-6 rounded-full transition-colors ${
            enabled ? 'bg-primary-600' : 'bg-gray-600'
          } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <span
            className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
              enabled ? 'translate-x-5' : 'translate-x-0'
            }`}
          />
        </button>
      </div>

      {/* Summary */}
      {environmentIds.length > 0 && browsers.length > 0 && (
        <div className="p-3 bg-gray-700/50 rounded-lg">
          <p className="text-sm font-medium text-gray-300 mb-2">
            Schedule will create {environmentIds.length * browsers.length} run{environmentIds.length * browsers.length !== 1 ? 's' : ''} per trigger:
          </p>
          <div className="flex flex-wrap gap-1">
            {environmentIds.map((envId) => {
              const env = environments.find((e) => e.id === envId)
              return browsers.map((browser) => (
                <span
                  key={`${envId}-${browser}`}
                  className="px-2 py-1 text-xs bg-gray-600 text-gray-200 rounded"
                >
                  {env?.name || 'Unknown'} / {browser}
                </span>
              ))
            })}
          </div>
        </div>
      )}

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
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              {isEditing ? 'Saving...' : 'Creating...'}
            </span>
          ) : (
            isEditing ? 'Save Changes' : 'Create Schedule'
          )}
        </button>
      </div>
    </form>
  )
}
