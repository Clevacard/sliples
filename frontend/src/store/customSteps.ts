import { create } from 'zustand'
import * as api from '../api/client'
import type { CustomStep, CustomStepCreate, CustomStepUpdate } from '../api/client'

interface CustomStepsState {
  // State
  steps: CustomStep[]
  selectedStep: CustomStep | null
  isLoading: boolean
  error: string | null

  // Actions
  fetchSteps: () => Promise<void>
  fetchStep: (id: string) => Promise<void>
  createStep: (data: CustomStepCreate) => Promise<CustomStep>
  updateStep: (id: string, data: CustomStepUpdate) => Promise<CustomStep>
  deleteStep: (id: string) => Promise<void>
  selectStep: (step: CustomStep | null) => void
  clearError: () => void
}

export const useCustomStepsStore = create<CustomStepsState>((set) => ({
  // Initial state
  steps: [],
  selectedStep: null,
  isLoading: false,
  error: null,

  // Fetch all custom steps
  fetchSteps: async () => {
    set({ isLoading: true, error: null })
    try {
      const steps = await api.listCustomSteps()
      set({ steps, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch custom steps:', error)
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch custom steps',
        isLoading: false,
      })
    }
  },

  // Fetch single custom step
  fetchStep: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const step = await api.getCustomStep(id)
      set({ selectedStep: step, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch custom step:', error)
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch custom step',
        isLoading: false,
      })
    }
  },

  // Create custom step
  createStep: async (data: CustomStepCreate) => {
    set({ isLoading: true, error: null })
    try {
      const step = await api.createCustomStep(data)
      set((state) => ({
        steps: [...state.steps, step],
        isLoading: false,
      }))
      return step
    } catch (error) {
      console.error('Failed to create custom step:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create custom step'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Update custom step
  updateStep: async (id: string, data: CustomStepUpdate) => {
    set({ isLoading: true, error: null })
    try {
      const step = await api.updateCustomStep(id, data)
      set((state) => ({
        steps: state.steps.map((s) => (s.id === id ? step : s)),
        selectedStep: state.selectedStep?.id === id ? step : state.selectedStep,
        isLoading: false,
      }))
      return step
    } catch (error) {
      console.error('Failed to update custom step:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to update custom step'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Delete custom step
  deleteStep: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.deleteCustomStep(id)
      set((state) => ({
        steps: state.steps.filter((s) => s.id !== id),
        selectedStep: state.selectedStep?.id === id ? null : state.selectedStep,
        isLoading: false,
      }))
    } catch (error) {
      console.error('Failed to delete custom step:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete custom step'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Select step
  selectStep: (step: CustomStep | null) => {
    set({ selectedStep: step })
  },

  // Clear error
  clearError: () => set({ error: null }),
}))
