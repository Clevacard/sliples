import { useState, useEffect } from 'react'
import KeyValueEditor, { KeyValuePair } from './KeyValueEditor'
import type { Environment, EnvironmentCreate, EnvironmentUpdate } from '../api/client'

interface EnvironmentFormProps {
  environment?: Environment | null
  onSubmit: (data: EnvironmentCreate | EnvironmentUpdate) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

// Convert Record<string, string> to KeyValuePair[]
function recordToPairs(record: Record<string, string>): KeyValuePair[] {
  return Object.entries(record).map(([key, value]) => ({ key, value }))
}

// Convert KeyValuePair[] to Record<string, string>
function pairsToRecord(pairs: KeyValuePair[]): Record<string, string> {
  return pairs.reduce((acc, { key, value }) => {
    if (key.trim()) {
      acc[key.trim()] = value
    }
    return acc
  }, {} as Record<string, string>)
}

// Simple URL validation
function isValidUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

export default function EnvironmentForm({
  environment,
  onSubmit,
  onCancel,
  isLoading = false,
}: EnvironmentFormProps) {
  const [name, setName] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [locale, setLocale] = useState('en-GB')
  const [timezoneId, setTimezoneId] = useState('Europe/London')
  const [variables, setVariables] = useState<KeyValuePair[]>([])
  const [retentionDays, setRetentionDays] = useState(365)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const isEditing = !!environment

  // Initialize form with environment data
  useEffect(() => {
    if (environment) {
      setName(environment.name)
      setBaseUrl(environment.base_url)
      setLocale(environment.locale || 'en-GB')
      setTimezoneId(environment.timezone_id || 'Europe/London')
      setVariables(recordToPairs(environment.variables || {}))
      setRetentionDays(environment.retention_days || 365)
    } else {
      setName('')
      setBaseUrl('')
      setLocale('en-GB')
      setTimezoneId('Europe/London')
      setVariables([])
      setRetentionDays(365)
    }
    setErrors({})
  }, [environment])

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!baseUrl.trim()) {
      newErrors.baseUrl = 'Base URL is required'
    } else if (!isValidUrl(baseUrl)) {
      newErrors.baseUrl = 'Please enter a valid URL'
    }

    if (retentionDays < 1 || retentionDays > 3650) {
      newErrors.retentionDays = 'Retention days must be between 1 and 3650'
    }

    // Check for duplicate keys in variables
    const keys = variables.map((p) => p.key.trim()).filter(Boolean)
    const uniqueKeys = new Set(keys)
    if (keys.length !== uniqueKeys.size) {
      newErrors.variables = 'Duplicate variable keys are not allowed'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    const data = {
      name: name.trim(),
      base_url: baseUrl.trim(),
      locale: locale.trim(),
      timezone_id: timezoneId.trim(),
      variables: pairsToRecord(variables),
      retention_days: retentionDays,
    }

    await onSubmit(data)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Name */}
      <div>
        <label htmlFor="env-name" className="block text-sm font-medium text-gray-300 mb-1">
          Name <span className="text-red-400">*</span>
        </label>
        <input
          id="env-name"
          type="text"
          className={`w-full px-3 py-2 bg-gray-700 border rounded-lg text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
            errors.name ? 'border-red-500' : 'border-gray-600'
          }`}
          placeholder="e.g., staging, production"
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={isLoading}
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-400">{errors.name}</p>
        )}
      </div>

      {/* Base URL */}
      <div>
        <label htmlFor="env-base-url" className="block text-sm font-medium text-gray-300 mb-1">
          Base URL <span className="text-red-400">*</span>
        </label>
        <input
          id="env-base-url"
          type="url"
          className={`w-full px-3 py-2 bg-gray-700 border rounded-lg text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
            errors.baseUrl ? 'border-red-500' : 'border-gray-600'
          }`}
          placeholder="https://staging.example.com"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          disabled={isLoading}
        />
        {errors.baseUrl && (
          <p className="mt-1 text-sm text-red-400">{errors.baseUrl}</p>
        )}
      </div>

      {/* Locale and Timezone */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="env-locale" className="block text-sm font-medium text-gray-300 mb-1">
            Browser Locale
          </label>
          <select
            id="env-locale"
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            value={locale}
            onChange={(e) => setLocale(e.target.value)}
            disabled={isLoading}
          >
            <option value="en-GB">English (UK)</option>
            <option value="en-US">English (US)</option>
            <option value="de-DE">German</option>
            <option value="fr-FR">French</option>
            <option value="es-ES">Spanish</option>
            <option value="it-IT">Italian</option>
            <option value="pt-BR">Portuguese (Brazil)</option>
            <option value="nl-NL">Dutch</option>
            <option value="pl-PL">Polish</option>
            <option value="ar-SA">Arabic (Saudi Arabia)</option>
            <option value="he-IL">Hebrew</option>
            <option value="zh-CN">Chinese (Simplified)</option>
            <option value="ja-JP">Japanese</option>
            <option value="ko-KR">Korean</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Affects number/date formatting and text direction (LTR/RTL)
          </p>
        </div>
        <div>
          <label htmlFor="env-timezone" className="block text-sm font-medium text-gray-300 mb-1">
            Timezone
          </label>
          <select
            id="env-timezone"
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            value={timezoneId}
            onChange={(e) => setTimezoneId(e.target.value)}
            disabled={isLoading}
          >
            <option value="Europe/London">Europe/London (GMT/BST)</option>
            <option value="Europe/Paris">Europe/Paris (CET)</option>
            <option value="Europe/Berlin">Europe/Berlin (CET)</option>
            <option value="America/New_York">America/New_York (EST)</option>
            <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
            <option value="America/Chicago">America/Chicago (CST)</option>
            <option value="America/Sao_Paulo">America/Sao_Paulo (BRT)</option>
            <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
            <option value="Asia/Shanghai">Asia/Shanghai (CST)</option>
            <option value="Asia/Dubai">Asia/Dubai (GST)</option>
            <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
            <option value="Asia/Riyadh">Asia/Riyadh (AST)</option>
            <option value="Australia/Sydney">Australia/Sydney (AEST)</option>
            <option value="UTC">UTC</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Browser timezone for date/time display
          </p>
        </div>
      </div>

      {/* Retention Days */}
      <div>
        <label htmlFor="env-retention" className="block text-sm font-medium text-gray-300 mb-1">
          Data Retention (days)
        </label>
        <input
          id="env-retention"
          type="number"
          min="1"
          max="3650"
          className={`w-full px-3 py-2 bg-gray-700 border rounded-lg text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
            errors.retentionDays ? 'border-red-500' : 'border-gray-600'
          }`}
          value={retentionDays}
          onChange={(e) => setRetentionDays(parseInt(e.target.value) || 365)}
          disabled={isLoading}
        />
        <p className="mt-1 text-xs text-gray-500">
          Test results older than this will be automatically deleted
        </p>
        {errors.retentionDays && (
          <p className="mt-1 text-sm text-red-400">{errors.retentionDays}</p>
        )}
      </div>

      {/* Variables */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Environment Variables
        </label>
        <p className="text-xs text-gray-500 mb-3">
          Define variables available to test scenarios in this environment. Sensitive values
          (containing password, secret, token, etc.) are automatically masked.
        </p>
        <KeyValueEditor
          pairs={variables}
          onChange={setVariables}
          keyPlaceholder="Variable name"
          valuePlaceholder="Value"
          disabled={isLoading}
        />
        {errors.variables && (
          <p className="mt-2 text-sm text-red-400">{errors.variables}</p>
        )}
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
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              {isEditing ? 'Saving...' : 'Creating...'}
            </span>
          ) : (
            isEditing ? 'Save Changes' : 'Create Environment'
          )}
        </button>
      </div>
    </form>
  )
}
