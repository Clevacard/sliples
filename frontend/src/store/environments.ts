import { create } from 'zustand'
import * as api from '../api/client'
import type { Environment, EnvironmentCreate, EnvironmentUpdate } from '../api/client'

interface EnvironmentsState {
  // State
  environments: Environment[]
  selectedEnvironment: Environment | null
  isLoading: boolean
  error: string | null

  // Actions
  fetchEnvironments: () => Promise<void>
  fetchEnvironment: (id: string) => Promise<void>
  createEnvironment: (data: EnvironmentCreate) => Promise<Environment>
  updateEnvironment: (id: string, data: EnvironmentUpdate) => Promise<Environment>
  deleteEnvironment: (id: string) => Promise<void>
  selectEnvironment: (environment: Environment | null) => void
  clearError: () => void
}

export const useEnvironmentsStore = create<EnvironmentsState>((set) => ({
  // Initial state
  environments: [],
  selectedEnvironment: null,
  isLoading: false,
  error: null,

  // Fetch all environments
  fetchEnvironments: async () => {
    set({ isLoading: true, error: null, selectedEnvironment: null })
    try {
      const environments = await api.getEnvironments()
      set({ environments, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch environments:', error)
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch environments',
        isLoading: false,
      })
    }
  },

  // Fetch single environment
  fetchEnvironment: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const environment = await api.getEnvironment(id)
      set({ selectedEnvironment: environment, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch environment:', error)
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch environment',
        isLoading: false,
      })
    }
  },

  // Create environment
  createEnvironment: async (data: EnvironmentCreate) => {
    set({ isLoading: true, error: null })
    try {
      const environment = await api.createEnvironment(data)
      set((state) => ({
        environments: [...state.environments, environment],
        isLoading: false,
      }))
      return environment
    } catch (error) {
      console.error('Failed to create environment:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create environment'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Update environment
  updateEnvironment: async (id: string, data: EnvironmentUpdate) => {
    set({ isLoading: true, error: null })
    try {
      const environment = await api.updateEnvironment(id, data)
      set((state) => ({
        environments: state.environments.map((env) =>
          env.id === id ? environment : env
        ),
        selectedEnvironment:
          state.selectedEnvironment?.id === id ? environment : state.selectedEnvironment,
        isLoading: false,
      }))
      return environment
    } catch (error) {
      console.error('Failed to update environment:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to update environment'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Delete environment
  deleteEnvironment: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.deleteEnvironment(id)
      set((state) => ({
        environments: state.environments.filter((env) => env.id !== id),
        selectedEnvironment:
          state.selectedEnvironment?.id === id ? null : state.selectedEnvironment,
        isLoading: false,
      }))
    } catch (error) {
      console.error('Failed to delete environment:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete environment'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Select environment
  selectEnvironment: (environment: Environment | null) => {
    set({ selectedEnvironment: environment })
  },

  // Clear error
  clearError: () => set({ error: null }),
}))
