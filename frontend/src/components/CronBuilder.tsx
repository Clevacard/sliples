import { useState, useEffect, useCallback } from 'react'
import { describeCron } from '../api/client'

interface CronBuilderProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

interface CronPreset {
  label: string
  expression: string
  description: string
}

const PRESETS: CronPreset[] = [
  { label: 'Every hour', expression: '0 * * * *', description: 'At minute 0 of every hour' },
  { label: 'Every 15 minutes', expression: '*/15 * * * *', description: 'Every 15 minutes' },
  { label: 'Every 30 minutes', expression: '*/30 * * * *', description: 'Every 30 minutes' },
  { label: 'Daily at 9:00 AM', expression: '0 9 * * *', description: 'Every day at 9:00 AM' },
  { label: 'Daily at midnight', expression: '0 0 * * *', description: 'Every day at midnight' },
  { label: 'Weekdays at 9:00 AM', expression: '0 9 * * 1-5', description: 'Monday through Friday at 9:00 AM' },
  { label: 'Weekly (Sunday midnight)', expression: '0 0 * * 0', description: 'Every Sunday at midnight' },
  { label: 'Monthly (1st at midnight)', expression: '0 0 1 * *', description: 'First day of every month at midnight' },
]

const MINUTES = Array.from({ length: 60 }, (_, i) => i)
const HOURS = Array.from({ length: 24 }, (_, i) => i)
const DAYS = Array.from({ length: 31 }, (_, i) => i + 1)
const MONTHS = [
  { value: '*', label: 'Every month' },
  { value: '1', label: 'January' },
  { value: '2', label: 'February' },
  { value: '3', label: 'March' },
  { value: '4', label: 'April' },
  { value: '5', label: 'May' },
  { value: '6', label: 'June' },
  { value: '7', label: 'July' },
  { value: '8', label: 'August' },
  { value: '9', label: 'September' },
  { value: '10', label: 'October' },
  { value: '11', label: 'November' },
  { value: '12', label: 'December' },
]
const WEEKDAYS = [
  { value: '*', label: 'Every day' },
  { value: '1-5', label: 'Weekdays (Mon-Fri)' },
  { value: '0,6', label: 'Weekends (Sat-Sun)' },
  { value: '0', label: 'Sunday' },
  { value: '1', label: 'Monday' },
  { value: '2', label: 'Tuesday' },
  { value: '3', label: 'Wednesday' },
  { value: '4', label: 'Thursday' },
  { value: '5', label: 'Friday' },
  { value: '6', label: 'Saturday' },
]

type CronMode = 'preset' | 'custom'

export default function CronBuilder({ value, onChange, disabled = false }: CronBuilderProps) {
  const [mode, setMode] = useState<CronMode>('preset')
  const [selectedPreset, setSelectedPreset] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [nextRuns, setNextRuns] = useState<string[]>([])
  const [validationError, setValidationError] = useState<string>('')

  // Custom cron parts
  const [minute, setMinute] = useState('0')
  const [hour, setHour] = useState('*')
  const [day, setDay] = useState('*')
  const [month, setMonth] = useState('*')
  const [weekday, setWeekday] = useState('*')

  // Parse initial value
  useEffect(() => {
    if (!value) return

    // Check if value matches a preset
    const preset = PRESETS.find((p) => p.expression === value)
    if (preset) {
      setMode('preset')
      setSelectedPreset(preset.expression)
    } else {
      setMode('custom')
      const parts = value.split(' ')
      if (parts.length === 5) {
        setMinute(parts[0])
        setHour(parts[1])
        setDay(parts[2])
        setMonth(parts[3])
        setWeekday(parts[4])
      }
    }
  }, []) // Only on mount

  // Fetch description from API
  const fetchDescription = useCallback(async (expression: string) => {
    if (!expression || expression.split(' ').length !== 5) {
      setDescription('')
      setNextRuns([])
      return
    }

    try {
      const result = await describeCron(expression)
      setDescription(result.description)
      setNextRuns(result.next_runs)
      setValidationError('')
    } catch (err) {
      setDescription('')
      setNextRuns([])
      setValidationError('Invalid cron expression')
    }
  }, [])

  // Update description when value changes
  useEffect(() => {
    if (value) {
      fetchDescription(value)
    }
  }, [value, fetchDescription])

  // Handle preset selection
  const handlePresetChange = (expression: string) => {
    setSelectedPreset(expression)
    onChange(expression)
  }

  // Handle custom cron change
  const updateCustomCron = (
    newMinute: string,
    newHour: string,
    newDay: string,
    newMonth: string,
    newWeekday: string
  ) => {
    const expression = `${newMinute} ${newHour} ${newDay} ${newMonth} ${newWeekday}`
    onChange(expression)
  }

  const handleMinuteChange = (val: string) => {
    setMinute(val)
    updateCustomCron(val, hour, day, month, weekday)
  }

  const handleHourChange = (val: string) => {
    setHour(val)
    updateCustomCron(minute, val, day, month, weekday)
  }

  const handleDayChange = (val: string) => {
    setDay(val)
    updateCustomCron(minute, hour, val, month, weekday)
  }

  const handleMonthChange = (val: string) => {
    setMonth(val)
    updateCustomCron(minute, hour, day, val, weekday)
  }

  const handleWeekdayChange = (val: string) => {
    setWeekday(val)
    updateCustomCron(minute, hour, day, month, val)
  }

  const formatNextRun = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleString()
  }

  return (
    <div className="space-y-4">
      {/* Mode Toggle */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setMode('preset')}
          disabled={disabled}
          className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
            mode === 'preset'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          Presets
        </button>
        <button
          type="button"
          onClick={() => setMode('custom')}
          disabled={disabled}
          className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
            mode === 'custom'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          Custom
        </button>
      </div>

      {/* Preset Mode */}
      {mode === 'preset' && (
        <div className="grid grid-cols-2 gap-2">
          {PRESETS.map((preset) => (
            <button
              key={preset.expression}
              type="button"
              onClick={() => handlePresetChange(preset.expression)}
              disabled={disabled}
              className={`px-3 py-2 text-left rounded-lg border transition-colors ${
                selectedPreset === preset.expression
                  ? 'border-primary-500 bg-primary-500/10 text-primary-300'
                  : 'border-gray-600 bg-gray-700 text-gray-300 hover:border-gray-500'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="font-medium text-sm">{preset.label}</div>
              <div className="text-xs text-gray-400 mt-0.5">{preset.description}</div>
            </button>
          ))}
        </div>
      )}

      {/* Custom Mode */}
      {mode === 'custom' && (
        <div className="space-y-4">
          <div className="grid grid-cols-5 gap-3">
            {/* Minute */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Minute</label>
              <select
                value={minute}
                onChange={(e) => handleMinuteChange(e.target.value)}
                disabled={disabled}
                className="w-full px-2 py-1.5 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="*">Every (*)</option>
                <option value="*/5">Every 5 (*/5)</option>
                <option value="*/10">Every 10 (*/10)</option>
                <option value="*/15">Every 15 (*/15)</option>
                <option value="*/30">Every 30 (*/30)</option>
                {MINUTES.map((m) => (
                  <option key={m} value={String(m)}>{m}</option>
                ))}
              </select>
            </div>

            {/* Hour */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Hour</label>
              <select
                value={hour}
                onChange={(e) => handleHourChange(e.target.value)}
                disabled={disabled}
                className="w-full px-2 py-1.5 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="*">Every (*)</option>
                <option value="*/2">Every 2 (*/2)</option>
                <option value="*/4">Every 4 (*/4)</option>
                <option value="*/6">Every 6 (*/6)</option>
                <option value="*/12">Every 12 (*/12)</option>
                {HOURS.map((h) => (
                  <option key={h} value={String(h)}>{h}:00</option>
                ))}
              </select>
            </div>

            {/* Day of Month */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Day</label>
              <select
                value={day}
                onChange={(e) => handleDayChange(e.target.value)}
                disabled={disabled}
                className="w-full px-2 py-1.5 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="*">Every (*)</option>
                {DAYS.map((d) => (
                  <option key={d} value={String(d)}>{d}</option>
                ))}
              </select>
            </div>

            {/* Month */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Month</label>
              <select
                value={month}
                onChange={(e) => handleMonthChange(e.target.value)}
                disabled={disabled}
                className="w-full px-2 py-1.5 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {MONTHS.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>

            {/* Day of Week */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Weekday</label>
              <select
                value={weekday}
                onChange={(e) => handleWeekdayChange(e.target.value)}
                disabled={disabled}
                className="w-full px-2 py-1.5 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {WEEKDAYS.map((w) => (
                  <option key={w.value} value={w.value}>{w.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Raw Expression */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Expression</label>
            <input
              type="text"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              disabled={disabled}
              placeholder="* * * * *"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Format: minute hour day month weekday (e.g., 0 9 * * 1-5 for weekdays at 9 AM)
            </p>
          </div>
        </div>
      )}

      {/* Description & Validation */}
      {validationError ? (
        <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg">
          <p className="text-sm text-red-400">{validationError}</p>
        </div>
      ) : description ? (
        <div className="p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-4 h-4 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm font-medium text-gray-200">{description}</span>
          </div>
          {nextRuns.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-gray-400 mb-1">Next runs:</p>
              <div className="space-y-0.5">
                {nextRuns.slice(0, 3).map((run, i) => (
                  <p key={i} className="text-xs text-gray-500">{formatNextRun(run)}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  )
}
