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
  successMessage: string | null

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
  clearSuccess: () => void
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
  successMessage: null,

  // Actions
  loadFileTree: async () => {
    set({ loadingTree: true, error: null })
    try {
      const [scenarios] = await Promise.all([
        getScenarios(),
        getRepos(),
      ])

      const scenarioList = Array.isArray(scenarios) ? scenarios : scenarios.items || []

      // Build tree structure from folder paths
      const root: FileTreeNode = {
        id: 'root',
        name: 'scenarios',
        type: 'folder',
        path: 'scenarios',
        children: [],
        expanded: true,
      }

      // Helper to find or create a folder node at a given path
      const getOrCreateFolder = (parentNode: FileTreeNode, pathParts: string[], currentPath: string): FileTreeNode => {
        if (pathParts.length === 0) return parentNode

        const folderName = pathParts[0]
        const folderPath = currentPath ? `${currentPath}/${folderName}` : folderName
        const folderId = `folder-${folderPath}`

        let folderNode = parentNode.children?.find((n) => n.id === folderId)
        if (!folderNode) {
          folderNode = {
            id: folderId,
            name: folderName,
            type: 'folder',
            path: folderPath,
            children: [],
            expanded: false,
          }
          parentNode.children = parentNode.children || []
          parentNode.children.push(folderNode)
        }

        // Recurse for remaining path parts
        return getOrCreateFolder(folderNode, pathParts.slice(1), folderPath)
      }

      // Group scenarios by feature file, then add to tree
      const featureMap = new Map<string, typeof scenarioList>()

      scenarioList.forEach((scenario: {
        id: string
        name: string
        feature_path: string
        repo_id?: string
        tags?: string[]
      }) => {
        const featurePath = scenario.feature_path || 'unknown.feature'
        if (!featureMap.has(featurePath)) {
          featureMap.set(featurePath, [])
        }
        featureMap.get(featurePath)!.push(scenario)
      })

      // Build tree from feature paths
      featureMap.forEach((scenarios, featurePath) => {
        // Parse path: "scenarios/giftstarr/homepage.feature" -> ["scenarios", "giftstarr", "homepage.feature"]
        const parts = featurePath.split('/').filter(Boolean)
        const fileName = parts.pop() || featurePath

        // Create folder structure
        const parentFolder = getOrCreateFolder(root, parts, '')

        // Create feature file node
        const featureNodeId = `feature-${featurePath}`
        let featureNode = parentFolder.children?.find((n) => n.id === featureNodeId)

        if (!featureNode) {
          featureNode = {
            id: featureNodeId,
            name: fileName,
            type: 'folder',
            path: featurePath,
            children: [],
            expanded: false,
          }
          parentFolder.children = parentFolder.children || []
          parentFolder.children.push(featureNode)
        }

        // Add scenarios as file nodes
        scenarios.forEach((scenario: { id: string; name: string; feature_path: string }) => {
          featureNode!.children = featureNode!.children || []
          featureNode!.children.push({
            id: `scenario-${scenario.id}`,
            name: scenario.name,
            type: 'file',
            path: `${featurePath}#${scenario.name}`,
            scenarioId: scenario.id,
          })
        })
      })

      // Sort children alphabetically at each level
      const sortChildren = (node: FileTreeNode) => {
        if (node.children) {
          node.children.sort((a, b) => {
            // Folders first, then files
            if (a.type !== b.type) {
              return a.type === 'folder' ? -1 : 1
            }
            return a.name.localeCompare(b.name)
          })
          node.children.forEach(sortChildren)
        }
      }
      sortChildren(root)

      // Use root's children as the tree (skip the root "scenarios" node if it only has one child)
      const tree = root.children && root.children.length === 1 && root.children[0].type === 'folder'
        ? [root.children[0]]
        : root.children || []

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

    // Clear current content immediately to avoid showing stale data
    set({ loading: true, error: null, content: '', originalContent: '' })
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
        isEditMode: true,  // Start in edit mode by default
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

    set({ saving: true, error: null, successMessage: null })
    try {
      await updateScenarioContent(currentFile.id, content)
      set({
        originalContent: content,
        isDirty: false,
        successMessage: 'Scenario saved successfully',
      })
      // Auto-clear success message after 3 seconds
      setTimeout(() => {
        set({ successMessage: null })
      }, 3000)
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

  clearSuccess: () => {
    set({ successMessage: null })
  },
}))
