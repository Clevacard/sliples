import { useEffect, useCallback, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import GherkinEditor from '../components/GherkinEditor'
import ScenarioTree from '../components/ScenarioTree'
import { useScenarioEditorStore } from '../store/scenarioEditor'
import { validateGherkinSteps, type ParseResponse, type StepValidation } from '../api/client'

export default function ScenarioEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const {
    currentFile,
    content,
    originalContent,
    isDirty,
    isEditMode,
    loading,
    saving,
    error,
    successMessage,
    loadFile,
    updateContent,
    saveFile,
    toggleEditMode,
    resetContent,
    clearFile,
    clearError,
    clearSuccess,
  } = useScenarioEditorStore()

  // Validation state
  const [validation, setValidation] = useState<ParseResponse | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [showPanel, setShowPanel] = useState(true)
  const [activeTab, setActiveTab] = useState<'validation' | 'changes'>('validation')
  const validationTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load file if ID is provided in URL
  useEffect(() => {
    if (id) {
      loadFile(id)
    } else {
      clearFile()
    }
  }, [id, loadFile, clearFile])

  // Debounced validation on content change
  useEffect(() => {
    if (!content) {
      setValidation(null)
      return
    }

    // Clear previous timeout
    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current)
    }

    // Debounce validation by 500ms
    validationTimeoutRef.current = setTimeout(async () => {
      setIsValidating(true)
      try {
        const result = await validateGherkinSteps(content)
        setValidation(result)
      } catch (err) {
        console.error('Validation failed:', err)
      } finally {
        setIsValidating(false)
      }
    }, 500)

    return () => {
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current)
      }
    }
  }, [content])

  // Listen for save shortcut from editor
  useEffect(() => {
    const handleSaveEvent = () => {
      if (isDirty && isEditMode) {
        handleSave()
      }
    }
    window.addEventListener('gherkin-editor-save', handleSaveEvent)
    return () => window.removeEventListener('gherkin-editor-save', handleSaveEvent)
  }, [isDirty, isEditMode])

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [isDirty])

  const handleSave = useCallback(async () => {
    try {
      await saveFile()
    } catch (err) {
      // Error is already set in store
    }
  }, [saveFile])

  const handleSelectScenario = useCallback((scenarioId: string) => {
    navigate(`/scenarios/${scenarioId}`)
  }, [navigate])

  const handleDiscard = useCallback(() => {
    if (isDirty) {
      const confirmed = window.confirm('Discard unsaved changes?')
      if (confirmed) {
        resetContent()
      }
    }
  }, [isDirty, resetContent])

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      {/* Success banner */}
      {successMessage && (
        <div className="bg-green-900/50 border border-green-700 text-green-200 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>{successMessage}</span>
          </div>
          <button onClick={clearSuccess} className="text-green-400 hover:text-green-300">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-2 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={clearError} className="text-red-400 hover:text-red-300">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - File Tree */}
        <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col overflow-hidden">
          <div className="p-3 border-b border-gray-700">
            <h2 className="text-sm font-semibold text-gray-300">Scenarios</h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            <ScenarioTree onSelectScenario={handleSelectScenario} />
          </div>
        </aside>

        {/* Main Editor Area */}
        <main className="flex-1 flex flex-col overflow-hidden bg-gray-900">
          {/* Toolbar */}
          <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
            <div className="flex items-center gap-3">
              {/* Back button */}
              <button
                onClick={() => navigate('/scenarios')}
                className="text-gray-400 hover:text-white transition-colors"
                title="Back to scenarios list"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>

              {/* File info */}
              {currentFile ? (
                <div className="flex items-center gap-2">
                  <span className="text-gray-300 font-medium">
                    {currentFile.name}
                    {isDirty && <span className="text-yellow-400 ml-1">*</span>}
                  </span>
                  <span className="text-gray-500 text-sm font-mono">
                    {currentFile.featurePath}
                  </span>
                </div>
              ) : (
                <span className="text-gray-500">No file selected</span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {/* Tags */}
              {currentFile?.tags && currentFile.tags.length > 0 && (
                <div className="flex gap-1 mr-4">
                  {currentFile.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="badge badge-info text-xs">
                      @{tag}
                    </span>
                  ))}
                  {currentFile.tags.length > 3 && (
                    <span className="badge badge-pending text-xs">
                      +{currentFile.tags.length - 3}
                    </span>
                  )}
                </div>
              )}

              {/* Edit mode toggle */}
              <button
                onClick={toggleEditMode}
                disabled={!currentFile}
                className={`
                  flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition-colors
                  ${isEditMode
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }
                  disabled:opacity-50 disabled:cursor-not-allowed
                `}
                title={isEditMode ? 'Click to switch to read-only mode' : 'Click to enable editing'}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {isEditMode ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  )}
                </svg>
                {isEditMode ? 'Editing' : 'Read Only'}
              </button>

              {/* Discard button */}
              {isDirty && (
                <button
                  onClick={handleDiscard}
                  className="px-3 py-1.5 rounded text-sm font-medium bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
                >
                  Discard
                </button>
              )}

              {/* Save button */}
              <button
                onClick={handleSave}
                disabled={!isDirty || saving || !currentFile}
                className="btn btn-primary btn-sm flex items-center gap-2"
              >
                {saving ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Saving...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                    </svg>
                    Save
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Editor content */}
          <div className="flex-1 overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <svg className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <p className="text-gray-400">Loading file...</p>
                </div>
              </div>
            ) : currentFile ? (
              <div className="h-full flex">
                {/* Main editor */}
                <div className="flex-1">
                  <GherkinEditor
                    value={content}
                    onChange={updateContent}
                    readOnly={!isEditMode}
                    showMinimap={true}
                    showLineNumbers={true}
                    fontSize={14}
                  />
                </div>

                {/* Right panel - Validation or Diff */}
                {showPanel && (
                  <div className="w-80 border-l border-gray-700 flex flex-col bg-gray-800">
                    {/* Panel tabs */}
                    <div className="flex border-b border-gray-700">
                      <button
                        className={`flex-1 px-3 py-2 text-xs font-semibold uppercase transition-colors ${
                          activeTab === 'validation' ? 'bg-gray-700 text-gray-200' : 'text-gray-400 hover:bg-gray-700/50'
                        }`}
                        onClick={() => setActiveTab('validation')}
                      >
                        Validation
                        {validation && (
                          <span className={`ml-2 px-1.5 py-0.5 rounded text-[10px] ${
                            validation.unmatched_steps > 0
                              ? 'bg-yellow-500/30 text-yellow-400'
                              : 'bg-green-500/30 text-green-400'
                          }`}>
                            {validation.unmatched_steps > 0 ? validation.unmatched_steps : '✓'}
                          </span>
                        )}
                      </button>
                      {isDirty && (
                        <button
                          className={`flex-1 px-3 py-2 text-xs font-semibold uppercase transition-colors ${
                            activeTab === 'changes' ? 'bg-gray-700 text-gray-200' : 'text-gray-400 hover:bg-gray-700/50'
                          }`}
                          onClick={() => setActiveTab('changes')}
                        >
                          Changes
                          <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] bg-yellow-500/30 text-yellow-400">
                            •
                          </span>
                        </button>
                      )}
                      <button
                        onClick={() => setShowPanel(false)}
                        className="px-2 text-gray-500 hover:text-gray-300 transition-colors"
                        title="Hide panel"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>

                    {/* Panel content */}
                    <div className="flex-1 overflow-auto">
                      {activeTab === 'changes' && isDirty ? (
                        <div className="p-3">
                          <DiffView original={originalContent} modified={content} />
                        </div>
                      ) : (
                        <StepValidationPanel
                          validation={validation}
                          isValidating={isValidating}
                        />
                      )}
                    </div>
                  </div>
                )}

                {/* Show panel button when hidden */}
                {!showPanel && (
                  <button
                    onClick={() => setShowPanel(true)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 px-2 py-4 bg-gray-700 hover:bg-gray-600 rounded-l-lg border border-gray-600 border-r-0 transition-colors"
                    title="Show validation panel"
                  >
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <h3 className="text-lg font-medium text-gray-300 mb-2">Select a scenario to edit</h3>
                  <p className="text-gray-500 text-sm">
                    Choose a file from the sidebar or{' '}
                    <button onClick={() => navigate('/scenarios')} className="text-blue-400 hover:text-blue-300">
                      browse all scenarios
                    </button>
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Status bar */}
          <div className="flex items-center justify-between px-4 py-1 bg-gray-800 border-t border-gray-700 text-xs text-gray-500">
            <div className="flex items-center gap-4">
              {currentFile && (
                <>
                  <span>Gherkin</span>
                  <span>|</span>
                  <span className={isEditMode ? 'text-green-400' : ''}>{isEditMode ? 'Edit Mode' : 'Read Only'}</span>
                  {isDirty && (
                    <>
                      <span>|</span>
                      <span className="text-yellow-400">Unsaved changes</span>
                    </>
                  )}
                  {validation && (
                    <>
                      <span>|</span>
                      {isValidating ? (
                        <span className="text-blue-400">Validating...</span>
                      ) : validation.unmatched_steps > 0 ? (
                        <span className="text-yellow-400">
                          {validation.unmatched_steps} step{validation.unmatched_steps !== 1 ? 's' : ''} need implementation
                        </span>
                      ) : (
                        <span className="text-green-400">All {validation.total_steps} steps matched</span>
                      )}
                    </>
                  )}
                </>
              )}
            </div>
            <div className="flex items-center gap-4">
              {currentFile && (
                <>
                  <span>Lines: {content.split('\n').length}</span>
                  <span>|</span>
                  <span>Chars: {content.length}</span>
                </>
              )}
              <span>UTF-8</span>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

// Step validation panel component
interface StepValidationPanelProps {
  validation: ParseResponse | null
  isValidating: boolean
}

function StepValidationPanel({ validation, isValidating }: StepValidationPanelProps) {
  if (isValidating) {
    return (
      <div className="p-4 text-center">
        <svg className="w-6 h-6 animate-spin text-blue-500 mx-auto mb-2" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p className="text-gray-400 text-sm">Validating steps...</p>
      </div>
    )
  }

  if (!validation) {
    return (
      <div className="p-4 text-center text-gray-500 text-sm">
        <p>No steps to validate</p>
      </div>
    )
  }

  if (validation.total_steps === 0) {
    return (
      <div className="p-4 text-center text-gray-500 text-sm">
        <svg className="w-8 h-8 mx-auto mb-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p>No Gherkin steps found</p>
        <p className="text-xs mt-1">Add Given/When/Then steps to validate</p>
      </div>
    )
  }

  const unmatchedSteps = validation.steps.filter(s => !s.is_matched)
  const matchedSteps = validation.steps.filter(s => s.is_matched)

  return (
    <div className="p-3 space-y-4">
      {/* Summary */}
      <div className={`p-3 rounded-lg ${
        validation.unmatched_steps > 0
          ? 'bg-yellow-900/30 border border-yellow-700/50'
          : 'bg-green-900/30 border border-green-700/50'
      }`}>
        <div className="flex items-center gap-2">
          {validation.unmatched_steps > 0 ? (
            <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
          <div>
            <p className={`font-medium ${validation.unmatched_steps > 0 ? 'text-yellow-300' : 'text-green-300'}`}>
              {validation.unmatched_steps > 0
                ? `${validation.unmatched_steps} step${validation.unmatched_steps !== 1 ? 's' : ''} need${validation.unmatched_steps === 1 ? 's' : ''} implementation`
                : 'All steps matched'}
            </p>
            <p className="text-xs text-gray-400">
              {validation.matched_steps}/{validation.total_steps} steps have implementations
            </p>
          </div>
        </div>
      </div>

      {/* Unmatched steps */}
      {unmatchedSteps.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-yellow-400 uppercase mb-2 flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Needs Implementation
          </h4>
          <div className="space-y-2">
            {unmatchedSteps.map((step, idx) => (
              <div
                key={idx}
                className="p-2 bg-yellow-900/20 rounded border border-yellow-700/30 font-mono text-xs"
              >
                <div className="flex items-center gap-2 text-gray-500 mb-1">
                  <span>Line {step.line_number}</span>
                </div>
                <div className="text-gray-200">
                  <span className="text-purple-400">{step.keyword}</span>{' '}
                  <span>{step.text}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Matched steps */}
      {matchedSteps.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-green-400 uppercase mb-2 flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Matched ({matchedSteps.length})
          </h4>
          <div className="space-y-1">
            {matchedSteps.map((step, idx) => (
              <div
                key={idx}
                className="p-2 bg-gray-700/30 rounded font-mono text-xs group hover:bg-gray-700/50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="text-gray-300 truncate">
                    <span className="text-purple-400">{step.keyword}</span>{' '}
                    <span className="text-gray-400">{step.text}</span>
                  </div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                    step.match_source === 'custom'
                      ? 'bg-blue-500/20 text-blue-400'
                      : 'bg-gray-600 text-gray-400'
                  }`}>
                    {step.match_source === 'custom' ? 'custom' : 'builtin'}
                  </span>
                </div>
                {step.matched_pattern && (
                  <div className="text-[10px] text-gray-500 mt-1 opacity-0 group-hover:opacity-100 transition-opacity truncate">
                    {step.matched_pattern}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Simple diff view component
interface DiffViewProps {
  original: string
  modified: string
}

function DiffView({ original, modified }: DiffViewProps) {
  const originalLines = original.split('\n')
  const modifiedLines = modified.split('\n')

  // Simple line-by-line diff
  const maxLines = Math.max(originalLines.length, modifiedLines.length)
  const changes: Array<{
    type: 'unchanged' | 'added' | 'removed' | 'modified'
    lineNumber: number
    original?: string
    modified?: string
  }> = []

  for (let i = 0; i < maxLines; i++) {
    const origLine = originalLines[i]
    const modLine = modifiedLines[i]

    if (origLine === modLine) {
      // Skip unchanged lines in diff view for brevity
      continue
    } else if (origLine === undefined) {
      changes.push({ type: 'added', lineNumber: i + 1, modified: modLine })
    } else if (modLine === undefined) {
      changes.push({ type: 'removed', lineNumber: i + 1, original: origLine })
    } else {
      changes.push({ type: 'modified', lineNumber: i + 1, original: origLine, modified: modLine })
    }
  }

  if (changes.length === 0) {
    return (
      <p className="text-gray-500 text-sm">No changes detected</p>
    )
  }

  return (
    <div className="space-y-2 font-mono text-xs">
      {changes.map((change, idx) => (
        <div key={idx} className="rounded overflow-hidden">
          <div className="flex items-center gap-2 px-2 py-1 bg-gray-700 text-gray-400">
            <span>Line {change.lineNumber}</span>
            <span className={`
              px-1.5 py-0.5 rounded text-[10px] uppercase font-bold
              ${change.type === 'added' ? 'bg-green-900 text-green-300' : ''}
              ${change.type === 'removed' ? 'bg-red-900 text-red-300' : ''}
              ${change.type === 'modified' ? 'bg-yellow-900 text-yellow-300' : ''}
            `}>
              {change.type}
            </span>
          </div>
          {change.original !== undefined && (
            <div className="px-2 py-1 bg-red-900/30 text-red-300 border-l-2 border-red-500">
              - {change.original || '(empty)'}
            </div>
          )}
          {change.modified !== undefined && (
            <div className="px-2 py-1 bg-green-900/30 text-green-300 border-l-2 border-green-500">
              + {change.modified || '(empty)'}
            </div>
          )}
        </div>
      ))}
      <div className="text-gray-500 pt-2 border-t border-gray-700">
        {changes.length} change{changes.length !== 1 ? 's' : ''}
      </div>
    </div>
  )
}
