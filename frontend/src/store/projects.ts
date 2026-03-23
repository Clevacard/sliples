import { create } from 'zustand'
import {
  getProjects,
  createProject as apiCreateProject,
  updateProject as apiUpdateProject,
  deleteProject as apiDeleteProject,
  getProjectMembers,
  addProjectMember as apiAddProjectMember,
  updateProjectMemberRole as apiUpdateProjectMemberRole,
  removeProjectMember as apiRemoveProjectMember,
  Project,
  ProjectMember,
  ProjectCreate,
  ProjectUpdate,
  ProjectRole,
} from '../api/client'

interface ProjectsState {
  // Data
  projects: Project[]
  currentProject: Project | null
  currentProjectMembers: ProjectMember[]

  // UI State
  isLoading: boolean
  isLoadingMembers: boolean
  error: string | null

  // Actions
  fetchProjects: () => Promise<void>
  setCurrentProject: (project: Project | null) => void
  setCurrentProjectById: (projectId: string) => Promise<void>
  createProject: (data: ProjectCreate) => Promise<Project>
  updateProject: (id: string, data: ProjectUpdate) => Promise<Project>
  deleteProject: (id: string) => Promise<void>
  fetchProjectMembers: (projectId: string) => Promise<void>
  addMember: (projectId: string, email: string, role: ProjectRole) => Promise<ProjectMember>
  updateMemberRole: (projectId: string, userId: string, role: ProjectRole) => Promise<ProjectMember>
  removeMember: (projectId: string, userId: string) => Promise<void>
  clearError: () => void
}

export const useProjectsStore = create<ProjectsState>()((set, get) => ({
  // Initial state
  projects: [],
  currentProject: null,
  currentProjectMembers: [],
  isLoading: false,
  isLoadingMembers: false,
  error: null,

  fetchProjects: async () => {
    set({ isLoading: true, error: null })
    try {
      const projects = await getProjects()
      set({ projects })

      // If no current project but we have projects, auto-select
      const { currentProject } = get()
      if (!currentProject && projects.length > 0) {
        // Try to restore from localStorage
        const savedId = localStorage.getItem('sliples_current_project_id')
        const savedProject = savedId ? projects.find(p => p.id === savedId) : null
        set({ currentProject: savedProject || projects[0] })
        if (savedProject || projects[0]) {
          localStorage.setItem('sliples_current_project_id', (savedProject || projects[0]).id)
        }
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch projects'
      set({ error: message })
    } finally {
      set({ isLoading: false })
    }
  },

  setCurrentProject: (project) => {
    set({ currentProject: project, currentProjectMembers: [] })
    if (project) {
      localStorage.setItem('sliples_current_project_id', project.id)
    } else {
      localStorage.removeItem('sliples_current_project_id')
    }
  },

  setCurrentProjectById: async (projectId) => {
    const { projects, fetchProjects } = get()
    let project = projects.find(p => p.id === projectId)

    if (!project) {
      // Fetch projects if not loaded
      await fetchProjects()
      project = get().projects.find(p => p.id === projectId)
    }

    if (project) {
      set({ currentProject: project, currentProjectMembers: [] })
      localStorage.setItem('sliples_current_project_id', project.id)
    }
  },

  createProject: async (data) => {
    set({ isLoading: true, error: null })
    try {
      const project = await apiCreateProject(data)
      set((state) => ({
        projects: [...state.projects, project],
        currentProject: project,
      }))
      localStorage.setItem('sliples_current_project_id', project.id)
      return project
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create project'
      set({ error: message })
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  updateProject: async (id, data) => {
    set({ isLoading: true, error: null })
    try {
      const updated = await apiUpdateProject(id, data)
      set((state) => ({
        projects: state.projects.map(p => p.id === id ? { ...p, ...updated } : p),
        currentProject: state.currentProject?.id === id ? { ...state.currentProject, ...updated } : state.currentProject,
      }))
      return updated
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update project'
      set({ error: message })
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  deleteProject: async (id) => {
    set({ isLoading: true, error: null })
    try {
      await apiDeleteProject(id)
      const { projects, currentProject } = get()
      const newProjects = projects.filter(p => p.id !== id)
      set({
        projects: newProjects,
        currentProject: currentProject?.id === id ? (newProjects[0] || null) : currentProject,
      })
      if (currentProject?.id === id && newProjects[0]) {
        localStorage.setItem('sliples_current_project_id', newProjects[0].id)
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete project'
      set({ error: message })
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  fetchProjectMembers: async (projectId) => {
    set({ isLoadingMembers: true, error: null })
    try {
      const members = await getProjectMembers(projectId)
      set({ currentProjectMembers: members })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch project members'
      set({ error: message })
    } finally {
      set({ isLoadingMembers: false })
    }
  },

  addMember: async (projectId, email, role) => {
    set({ isLoadingMembers: true, error: null })
    try {
      const member = await apiAddProjectMember(projectId, email, role)
      set((state) => ({
        currentProjectMembers: [...state.currentProjectMembers, member],
        projects: state.projects.map(p =>
          p.id === projectId ? { ...p, member_count: (p.member_count || 0) + 1 } : p
        ),
      }))
      return member
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to add member'
      set({ error: message })
      throw error
    } finally {
      set({ isLoadingMembers: false })
    }
  },

  updateMemberRole: async (projectId, userId, role) => {
    set({ isLoadingMembers: true, error: null })
    try {
      const updated = await apiUpdateProjectMemberRole(projectId, userId, role)
      set((state) => ({
        currentProjectMembers: state.currentProjectMembers.map(m =>
          m.user_id === userId ? { ...m, role: updated.role } : m
        ),
      }))
      return updated
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update member role'
      set({ error: message })
      throw error
    } finally {
      set({ isLoadingMembers: false })
    }
  },

  removeMember: async (projectId, userId) => {
    set({ isLoadingMembers: true, error: null })
    try {
      await apiRemoveProjectMember(projectId, userId)
      set((state) => ({
        currentProjectMembers: state.currentProjectMembers.filter(m => m.user_id !== userId),
        projects: state.projects.map(p =>
          p.id === projectId ? { ...p, member_count: Math.max(0, (p.member_count || 1) - 1) } : p
        ),
      }))
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to remove member'
      set({ error: message })
      throw error
    } finally {
      set({ isLoadingMembers: false })
    }
  },

  clearError: () => set({ error: null }),
}))
