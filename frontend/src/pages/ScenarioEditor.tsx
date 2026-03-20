import { useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import GherkinEditor from '../components/GherkinEditor'
import ScenarioTree from '../components/ScenarioTree'
import { useScenarioEditorStore } from '../store/scenarioEditor'

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

  // Load file if ID is provided in URL
  useEffect(() => {
    if (id) {
      loadFile(id)
    } else {
      clearFile()
    }
  }, [id, loadFile, clearFile])

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
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }
                  disabled:opacity-50 disabled:cursor-not-allowed
                `}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {isEditMode ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  )}
                </svg>
                {isEditMode ? 'Viewing' : 'Edit'}
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

                {/* Diff view when dirty */}
                {isDirty && isEditMode && (
                  <div className="w-80 border-l border-gray-700 flex flex-col bg-gray-800">
                    <div className="px-3 py-2 border-b border-gray-700">
                      <h3 className="text-xs font-semibold text-gray-400 uppercase">Changes</h3>
                    </div>
                    <div className="flex-1 overflow-auto p-3">
                      <DiffView original={originalContent} modified={content} />
                    </div>
                  </div>
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
                  <span>{isEditMode ? 'Edit Mode' : 'Read Only'}</span>
                  {isDirty && (
                    <>
                      <span>|</span>
                      <span className="text-yellow-400">Unsaved changes</span>
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
