import { useState } from 'react'

export interface KeyValuePair {
  key: string
  value: string
}

interface KeyValueEditorProps {
  pairs: KeyValuePair[]
  onChange: (pairs: KeyValuePair[]) => void
  keyPlaceholder?: string
  valuePlaceholder?: string
  sensitiveKeys?: string[]
  disabled?: boolean
}

// Keys that should be masked by default
const DEFAULT_SENSITIVE_PATTERNS = [
  /password/i,
  /secret/i,
  /token/i,
  /api.?key/i,
  /credential/i,
  /auth/i,
]

function isSensitiveKey(key: string, sensitiveKeys?: string[]): boolean {
  if (sensitiveKeys?.some((sk) => key.toLowerCase().includes(sk.toLowerCase()))) {
    return true
  }
  return DEFAULT_SENSITIVE_PATTERNS.some((pattern) => pattern.test(key))
}

export default function KeyValueEditor({
  pairs,
  onChange,
  keyPlaceholder = 'Key',
  valuePlaceholder = 'Value',
  sensitiveKeys,
  disabled = false,
}: KeyValueEditorProps) {
  const [visibleValues, setVisibleValues] = useState<Set<number>>(new Set())

  const handleKeyChange = (index: number, newKey: string) => {
    const updated = pairs.map((pair, i) =>
      i === index ? { ...pair, key: newKey } : pair
    )
    onChange(updated)
  }

  const handleValueChange = (index: number, newValue: string) => {
    const updated = pairs.map((pair, i) =>
      i === index ? { ...pair, value: newValue } : pair
    )
    onChange(updated)
  }

  const handleAddPair = () => {
    onChange([...pairs, { key: '', value: '' }])
  }

  const handleRemovePair = (index: number) => {
    onChange(pairs.filter((_, i) => i !== index))
    setVisibleValues((prev) => {
      const next = new Set(prev)
      next.delete(index)
      return next
    })
  }

  const toggleValueVisibility = (index: number) => {
    setVisibleValues((prev) => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  return (
    <div className="space-y-3">
      {pairs.length === 0 ? (
        <p className="text-sm text-gray-500 italic">No variables defined</p>
      ) : (
        pairs.map((pair, index) => {
          const isSensitive = isSensitiveKey(pair.key, sensitiveKeys)
          const isValueVisible = visibleValues.has(index) || !isSensitive

          return (
            <div key={index} className="flex items-center gap-2">
              {/* Key Input */}
              <input
                type="text"
                className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                placeholder={keyPlaceholder}
                value={pair.key}
                onChange={(e) => handleKeyChange(index, e.target.value)}
                disabled={disabled}
              />

              {/* Value Input */}
              <div className="flex-1 relative">
                <input
                  type={isValueVisible ? 'text' : 'password'}
                  className="w-full px-3 py-2 pr-10 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                  placeholder={valuePlaceholder}
                  value={pair.value}
                  onChange={(e) => handleValueChange(index, e.target.value)}
                  disabled={disabled}
                />
                {isSensitive && (
                  <button
                    type="button"
                    onClick={() => toggleValueVisibility(index)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-200 transition-colors"
                    title={isValueVisible ? 'Hide value' : 'Show value'}
                    disabled={disabled}
                  >
                    {isValueVisible ? (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                )}
              </div>

              {/* Remove Button */}
              <button
                type="button"
                onClick={() => handleRemovePair(index)}
                className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg transition-colors"
                title="Remove"
                disabled={disabled}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          )
        })
      )}

      {/* Add Button */}
      <button
        type="button"
        onClick={handleAddPair}
        className="flex items-center gap-2 px-3 py-2 text-sm text-primary-400 hover:text-primary-300 hover:bg-gray-700 rounded-lg transition-colors"
        disabled={disabled}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Add Variable
      </button>
    </div>
  )
}
