import { create } from 'zustand'
import * as api from '../api/client'
import type { Schedule, ScheduleCreate, ScheduleUpdate } from '../api/client'

interface SchedulesState {
  // State
  schedules: Schedule[]
  selectedSchedule: Schedule | null
  isLoading: boolean
  error: string | null

  // Actions
  fetchSchedules: () => Promise<void>
  fetchSchedule: (id: string) => Promise<void>
  createSchedule: (data: ScheduleCreate) => Promise<Schedule>
  updateSchedule: (id: string, data: ScheduleUpdate) => Promise<Schedule>
  deleteSchedule: (id: string) => Promise<void>
  toggleSchedule: (id: string) => Promise<Schedule>
  runScheduleNow: (id: string) => Promise<void>
  selectSchedule: (schedule: Schedule | null) => void
  clearError: () => void
}

export const useSchedulesStore = create<SchedulesState>((set, get) => ({
  // Initial state
  schedules: [],
  selectedSchedule: null,
  isLoading: false,
  error: null,

  // Fetch all schedules
  fetchSchedules: async () => {
    set({ isLoading: true, error: null })
    try {
      const schedules = await api.listSchedules()
      set({ schedules, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch schedules:', error)
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch schedules',
        isLoading: false,
      })
    }
  },

  // Fetch single schedule
  fetchSchedule: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const schedule = await api.getSchedule(id)
      set({ selectedSchedule: schedule, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch schedule:', error)
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch schedule',
        isLoading: false,
      })
    }
  },

  // Create schedule
  createSchedule: async (data: ScheduleCreate) => {
    set({ isLoading: true, error: null })
    try {
      const schedule = await api.createSchedule(data)
      set((state) => ({
        schedules: [schedule, ...state.schedules],
        isLoading: false,
      }))
      return schedule
    } catch (error) {
      console.error('Failed to create schedule:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create schedule'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Update schedule
  updateSchedule: async (id: string, data: ScheduleUpdate) => {
    set({ isLoading: true, error: null })
    try {
      const schedule = await api.updateSchedule(id, data)
      set((state) => ({
        schedules: state.schedules.map((s) =>
          s.id === id ? schedule : s
        ),
        selectedSchedule:
          state.selectedSchedule?.id === id ? schedule : state.selectedSchedule,
        isLoading: false,
      }))
      return schedule
    } catch (error) {
      console.error('Failed to update schedule:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to update schedule'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Delete schedule
  deleteSchedule: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.deleteSchedule(id)
      set((state) => ({
        schedules: state.schedules.filter((s) => s.id !== id),
        selectedSchedule:
          state.selectedSchedule?.id === id ? null : state.selectedSchedule,
        isLoading: false,
      }))
    } catch (error) {
      console.error('Failed to delete schedule:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete schedule'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Toggle schedule enabled/disabled
  toggleSchedule: async (id: string) => {
    set({ error: null })
    try {
      const schedule = await api.toggleSchedule(id)
      set((state) => ({
        schedules: state.schedules.map((s) =>
          s.id === id ? schedule : s
        ),
        selectedSchedule:
          state.selectedSchedule?.id === id ? schedule : state.selectedSchedule,
      }))
      return schedule
    } catch (error) {
      console.error('Failed to toggle schedule:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to toggle schedule'
      set({ error: errorMessage })
      throw new Error(errorMessage)
    }
  },

  // Run schedule immediately
  runScheduleNow: async (id: string) => {
    set({ error: null })
    try {
      await api.runScheduleNow(id)
    } catch (error) {
      console.error('Failed to run schedule:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to run schedule'
      set({ error: errorMessage })
      throw new Error(errorMessage)
    }
  },

  // Select schedule
  selectSchedule: (schedule: Schedule | null) => {
    set({ selectedSchedule: schedule })
  },

  // Clear error
  clearError: () => set({ error: null }),
}))
