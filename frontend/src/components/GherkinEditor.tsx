import { useRef, useEffect } from 'react'
import Editor, { Monaco, OnMount } from '@monaco-editor/react'
import type * as monacoEditor from 'monaco-editor'

type IStandaloneCodeEditor = monacoEditor.editor.IStandaloneCodeEditor

interface GherkinEditorProps {
  value: string
  onChange?: (value: string) => void
  readOnly?: boolean
  height?: string | number
  showMinimap?: boolean
  showLineNumbers?: boolean
  fontSize?: number
}

// Register Gherkin language definition
function registerGherkinLanguage(monaco: Monaco) {
  // Check if already registered
  const languages = monaco.languages.getLanguages()
  if (languages.some((lang: { id: string }) => lang.id === 'gherkin')) {
    return
  }

  // Register the language
  monaco.languages.register({ id: 'gherkin' })

  // Define tokens for syntax highlighting
  monaco.languages.setMonarchTokensProvider('gherkin', {
    defaultToken: '',
    tokenPostfix: '.gherkin',

    keywords: [
      'Feature',
      'Background',
      'Scenario',
      'Scenario Outline',
      'Examples',
      'Given',
      'When',
      'Then',
      'And',
      'But',
      'Rule',
    ],

    tokenizer: {
      root: [
        // Comments
        [/#.*$/, 'comment'],

        // Tags
        [/@[\w-]+/, 'tag'],

        // Feature keyword
        [/^\s*(Feature):/, ['keyword.feature']],

        // Scenario keywords
        [/^\s*(Scenario Outline|Scenario|Background|Rule|Examples):/, ['keyword.scenario']],

        // Step keywords - must be at start of line (with optional whitespace)
        [/^\s*(Given|When|Then|And|But)\b/, 'keyword.step'],

        // Strings in double quotes
        [/"[^"]*"/, 'string'],

        // Strings in single quotes
        [/'[^']*'/, 'string'],

        // Numbers
        [/\b\d+\b/, 'number'],

        // Variables in angle brackets (for Scenario Outline)
        [/<[^>]+>/, 'variable'],

        // Table delimiter
        [/\|/, 'delimiter.table'],

        // Doc strings
        [/"""/, { token: 'string.docstring', next: '@docstring' }],
      ],

      docstring: [
        [/"""/, { token: 'string.docstring', next: '@pop' }],
        [/./, 'string.docstring'],
      ],
    },
  })

  // Define language configuration
  monaco.languages.setLanguageConfiguration('gherkin', {
    comments: {
      lineComment: '#',
    },
    brackets: [],
    autoClosingPairs: [
      { open: '"', close: '"' },
      { open: "'", close: "'" },
      { open: '<', close: '>' },
    ],
    surroundingPairs: [
      { open: '"', close: '"' },
      { open: "'", close: "'" },
      { open: '<', close: '>' },
    ],
    folding: {
      markers: {
        start: /^\s*(Feature|Scenario|Background|Rule):/,
        end: /^\s*$/,
      },
    },
  })

  // Register completion provider
  monaco.languages.registerCompletionItemProvider('gherkin', {
    provideCompletionItems: (model: monacoEditor.editor.ITextModel, position: monacoEditor.Position) => {
      const word = model.getWordUntilPosition(position)
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn,
      }

      const lineContent = model.getLineContent(position.lineNumber).trim()
      const isStartOfLine = lineContent.length === 0 || lineContent === word.word

      const suggestions: monacoEditor.languages.CompletionItem[] = []

      // Feature-level keywords
      if (isStartOfLine) {
        suggestions.push(
          {
            label: 'Feature',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'Feature: ${1:Feature Name}\n\n  ${0}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Define a new feature',
            range,
          },
          {
            label: 'Scenario',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'Scenario: ${1:Scenario Name}\n    Given ${2:precondition}\n    When ${3:action}\n    Then ${4:expected result}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Define a new scenario',
            range,
          },
          {
            label: 'Scenario Outline',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'Scenario Outline: ${1:Scenario Name}\n    Given ${2:precondition with <variable>}\n    When ${3:action with <variable>}\n    Then ${4:expected result}\n\n    Examples:\n      | ${5:variable} |\n      | ${6:value}    |',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Define a scenario with examples',
            range,
          },
          {
            label: 'Background',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'Background:\n    Given ${1:common precondition}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Define background steps for all scenarios',
            range,
          },
          {
            label: 'Given',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'Given ${1:precondition}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Define a precondition',
            range,
          },
          {
            label: 'When',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'When ${1:action}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Define an action',
            range,
          },
          {
            label: 'Then',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'Then ${1:expected result}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Define an expected result',
            range,
          },
          {
            label: 'And',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'And ${1:additional step}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Additional step',
            range,
          },
          {
            label: 'But',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'But ${1:exception}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Define an exception',
            range,
          },
          {
            label: 'Examples',
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: 'Examples:\n      | ${1:column1} | ${2:column2} |\n      | ${3:value1}  | ${4:value2}  |',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Define examples for Scenario Outline',
            range,
          },
          {
            label: '@tag',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: '@${1:tagname}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Add a tag',
            range,
          }
        )
      }

      // Common step patterns
      const stepPatterns = [
        { label: 'I am on the "{page}" page', detail: 'Navigate to page' },
        { label: 'I click on "{element}"', detail: 'Click action' },
        { label: 'I fill in "{field}" with "{value}"', detail: 'Fill input' },
        { label: 'I should see "{text}"', detail: 'Text assertion' },
        { label: 'I should see the "{element}" element', detail: 'Element assertion' },
        { label: 'I wait for {seconds} seconds', detail: 'Wait action' },
        { label: 'I am logged in as "{user}"', detail: 'Login step' },
        { label: 'the page title should be "{title}"', detail: 'Title assertion' },
        { label: 'I press Enter', detail: 'Keyboard action' },
        { label: 'the "{element}" should be visible', detail: 'Visibility assertion' },
        { label: 'the "{element}" should be disabled', detail: 'State assertion' },
        { label: 'I select "{option}" from "{dropdown}"', detail: 'Select action' },
        { label: 'I check the "{checkbox}" checkbox', detail: 'Checkbox action' },
        { label: 'I upload "{file}" to "{input}"', detail: 'File upload' },
        { label: 'I take a screenshot', detail: 'Screenshot action' },
      ]

      // Add step patterns if we're after a step keyword
      const stepKeywordMatch = lineContent.match(/^\s*(Given|When|Then|And|But)\s+/)
      if (stepKeywordMatch) {
        stepPatterns.forEach((pattern) => {
          suggestions.push({
            label: pattern.label,
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: pattern.label.replace(/\{([^}]+)\}/g, '${1:$1}'),
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            detail: pattern.detail,
            range: {
              ...range,
              startColumn: stepKeywordMatch[0].length + 1,
            },
          })
        })
      }

      return { suggestions }
    },
  })
}

// Define dark theme for Gherkin
function defineGherkinTheme(monaco: Monaco) {
  monaco.editor.defineTheme('gherkin-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
      { token: 'tag', foreground: 'CE9178' },
      { token: 'keyword.feature', foreground: '569CD6', fontStyle: 'bold' },
      { token: 'keyword.scenario', foreground: '4EC9B0', fontStyle: 'bold' },
      { token: 'keyword.step', foreground: 'C586C0' },
      { token: 'string', foreground: 'CE9178' },
      { token: 'string.docstring', foreground: 'CE9178' },
      { token: 'number', foreground: 'B5CEA8' },
      { token: 'variable', foreground: '9CDCFE' },
      { token: 'delimiter.table', foreground: 'D4D4D4' },
    ],
    colors: {
      'editor.background': '#1a1a2e',
      'editor.foreground': '#d4d4d4',
      'editor.lineHighlightBackground': '#2a2a40',
      'editor.selectionBackground': '#264f78',
      'editorLineNumber.foreground': '#858585',
      'editorLineNumber.activeForeground': '#c6c6c6',
      'editorCursor.foreground': '#aeafad',
      'editor.inactiveSelectionBackground': '#3a3d41',
    },
  })
}

export default function GherkinEditor({
  value,
  onChange,
  readOnly = false,
  height = '100%',
  showMinimap = true,
  showLineNumbers = true,
  fontSize = 14,
}: GherkinEditorProps) {
  const editorRef = useRef<IStandaloneCodeEditor | null>(null)

  const handleEditorWillMount = (monaco: Monaco) => {
    registerGherkinLanguage(monaco)
    defineGherkinTheme(monaco)
  }

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor

    // Configure editor
    editor.updateOptions({
      tabSize: 2,
      insertSpaces: true,
      detectIndentation: false,
    })

    // Add keyboard shortcuts
    editor.addAction({
      id: 'save-file',
      label: 'Save File',
      keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS],
      run: () => {
        // Trigger save via custom event
        const event = new CustomEvent('gherkin-editor-save')
        window.dispatchEvent(event)
      },
    })
  }

  const handleEditorChange = (newValue: string | undefined) => {
    if (onChange && newValue !== undefined) {
      onChange(newValue)
    }
  }

  // Update editor options when props change
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({
        readOnly,
        minimap: { enabled: showMinimap },
        lineNumbers: showLineNumbers ? 'on' : 'off',
        fontSize,
      })
    }
  }, [readOnly, showMinimap, showLineNumbers, fontSize])

  return (
    <Editor
      height={height}
      language="gherkin"
      value={value}
      onChange={handleEditorChange}
      theme="gherkin-dark"
      beforeMount={handleEditorWillMount}
      onMount={handleEditorDidMount}
      options={{
        readOnly,
        minimap: { enabled: showMinimap },
        lineNumbers: showLineNumbers ? 'on' : 'off',
        fontSize,
        wordWrap: 'on',
        automaticLayout: true,
        scrollBeyondLastLine: false,
        renderLineHighlight: 'all',
        cursorBlinking: 'smooth',
        smoothScrolling: true,
        padding: { top: 16, bottom: 16 },
        folding: true,
        foldingStrategy: 'indentation',
        showFoldingControls: 'mouseover',
        bracketPairColorization: { enabled: true },
        guides: {
          indentation: true,
          bracketPairs: false,
        },
        scrollbar: {
          verticalScrollbarSize: 10,
          horizontalScrollbarSize: 10,
        },
      }}
    />
  )
}
