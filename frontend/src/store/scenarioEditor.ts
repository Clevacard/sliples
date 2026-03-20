import { create } from 'zustand'
import { getScenarios, getRepos, getScenarioContent, updateScenarioContent } from '../api/client'

export interface FileTreeNode {
  id: string
  name: string
  type: 'repo' | 'folder' | 'file'
  path: string
  children?: FileTreeNode[]
  scenarioId?: string
  repoId?: string
  expanded?: boolean
}

export interface ScenarioFile {
  id: string
  name: string
  featurePath: string
  repoId?: string
  repoName?: string
  tags: string[]
}

interface ScenarioEditorState {
  // Current file state
  currentFile: ScenarioFile | null
  originalContent: string
  content: string
  isDirty: boolean
  isEditMode: boolean

  // File tree
  fileTree: FileTreeNode[]
  expandedNodes: Set<string>

  // UI state
  loading: boolean
  saving: boolean
  loadingTree: boolean
  error: string | null

  // Actions
  loadFileTree: () => Promise<void>
  loadFile: (scenarioId: string) => Promise<void>
  updateContent: (content: string) => void
  saveFile: () => Promise<void>
  toggleEditMode: () => void
  setEditMode: (enabled: boolean) => void
  toggleNode: (nodeId: string) => void
  expandNode: (nodeId: string) => void
  collapseNode: (nodeId: string) => void
  resetContent: () => void
  clearFile: () => void
  clearError: () => void
}

export const useScenarioEditorStore = create<ScenarioEditorState>((set, get) => ({
  // Initial state
  currentFile: null,
  originalContent: '',
  content: '',
  isDirty: false,
  isEditMode: false,
  fileTree: [],
  expandedNodes: new Set<string>(),
  loading: false,
  saving: false,
  loadingTree: false,
  error: null,

  // Actions
  loadFileTree: async () => {
    set({ loadingTree: true, error: null })
    try {
      const [scenarios, repos] = await Promise.all([
        getScenarios(),
        getRepos(),
      ])

      const scenarioList = Array.isArray(scenarios) ? scenarios : scenarios.items || []
      const repoList = Array.isArray(repos) ? repos : repos.items || []

      // Build tree structure: repos -> features -> scenarios
      const repoMap = new Map<string, FileTreeNode>()

      // Initialize repos
      repoList.forEach((repo: { id: string; name: string }) => {
        repoMap.set(repo.id, {
          id: `repo-${repo.id}`,
          name: repo.name,
          type: 'repo',
          path: repo.name,
          children: [],
          expanded: false,
        })
      })

      // Group scenarios by repo and feature path
      scenarioList.forEach((scenario: {
        id: string
        name: string
        feature_path: string
        repo_id?: string
        tags?: string[]
      }) => {
        const repoId = scenario.repo_id || 'unknown'
        let repoNode = repoMap.get(repoId)

        if (!repoNode) {
          repoNode = {
            id: `repo-${repoId}`,
            name: 'Unknown Repository',
            type: 'repo',
            path: 'unknown',
            children: [],
            expanded: false,
          }
          repoMap.set(repoId, repoNode)
        }

        // Find or create feature file node
        const featurePath = scenario.feature_path || 'unknown.feature'
        const featureNodeId = `feature-${repoId}-${featurePath}`
        let featureNode = repoNode.children?.find((n) => n.id === featureNodeId)

        if (!featureNode) {
          featureNode = {
            id: featureNodeId,
            name: featurePath.split('/').pop() || featurePath,
            type: 'folder',
            path: featurePath,
            children: [],
            repoId,
            expanded: false,
          }
          repoNode.children?.push(featureNode)
        }

        // Add scenario as file node
        featureNode.children?.push({
          id: `scenario-${scenario.id}`,
          name: scenario.name,
          type: 'file',
          path: `${featurePath}#${scenario.name}`,
          scenarioId: scenario.id,
          repoId,
        })
      })

      const tree = Array.from(repoMap.values())
      set({ fileTree: tree })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load file tree'
      set({ error: message })
    } finally {
      set({ loadingTree: false })
    }
  },

  loadFile: async (scenarioId: string) => {
    const { isDirty, currentFile } = get()

    // Warn if there are unsaved changes
    if (isDirty && currentFile) {
      const confirmed = window.confirm('You have unsaved changes. Discard them?')
      if (!confirmed) return
    }

    set({ loading: true, error: null })
    try {
      const data = await getScenarioContent(scenarioId)
      set({
        currentFile: {
          id: data.id,
          name: data.name,
          featurePath: data.feature_path,
          repoId: data.repo_id,
          repoName: data.repo_name,
          tags: data.tags || [],
        },
        originalContent: data.content || '',
        content: data.content || '',
        isDirty: false,
        isEditMode: false,
      })

      // Auto-expand nodes to show the file
      const { expandNode } = get()
      if (data.repo_id) {
        expandNode(`repo-${data.repo_id}`)
        expandNode(`feature-${data.repo_id}-${data.feature_path}`)
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load file'
      set({ error: message })
    } finally {
      set({ loading: false })
    }
  },

  updateContent: (content: string) => {
    const { originalContent } = get()
    set({
      content,
      isDirty: content !== originalContent,
    })
  },

  saveFile: async () => {
    const { currentFile, content } = get()
    if (!currentFile) return

    set({ saving: true, error: null })
    try {
      await updateScenarioContent(currentFile.id, content)
      set({
        originalContent: content,
        isDirty: false,
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save file'
      set({ error: message })
      throw error
    } finally {
      set({ saving: false })
    }
  },

  toggleEditMode: () => {
    set((state) => ({ isEditMode: !state.isEditMode }))
  },

  setEditMode: (enabled: boolean) => {
    set({ isEditMode: enabled })
  },

  toggleNode: (nodeId: string) => {
    set((state) => {
      const newExpanded = new Set(state.expandedNodes)
      if (newExpanded.has(nodeId)) {
        newExpanded.delete(nodeId)
      } else {
        newExpanded.add(nodeId)
      }
      return { expandedNodes: newExpanded }
    })
  },

  expandNode: (nodeId: string) => {
    set((state) => {
      const newExpanded = new Set(state.expandedNodes)
      newExpanded.add(nodeId)
      return { expandedNodes: newExpanded }
    })
  },

  collapseNode: (nodeId: string) => {
    set((state) => {
      const newExpanded = new Set(state.expandedNodes)
      newExpanded.delete(nodeId)
      return { expandedNodes: newExpanded }
    })
  },

  resetContent: () => {
    const { originalContent } = get()
    set({
      content: originalContent,
      isDirty: false,
    })
  },

  clearFile: () => {
    set({
      currentFile: null,
      originalContent: '',
      content: '',
      isDirty: false,
      isEditMode: false,
    })
  },

  clearError: () => {
    set({ error: null })
  },
}))
