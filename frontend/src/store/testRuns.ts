import { create } from 'zustand'
import { getTestRuns, getTestRun, createTestRun, getEnvironments, getBrowsers } from '../api/client'

export interface TestRun {
  id: string
  status: 'queued' | 'running' | 'passed' | 'failed' | 'cancelled'
  browser: string
  browser_version?: string
  environment_id: string
  environment_name?: string
  scenario_count?: number
  passed_count?: number
  failed_count?: number
  triggered_by?: string
  created_at: string
  started_at?: string
  finished_at?: string
}

export interface TestResult {
  id: string
  scenario_id?: string
  scenario_name?: string
  step_name: string
  status: 'passed' | 'failed' | 'skipped' | 'pending'
  duration_ms: number
  error_message?: string
  screenshot_url?: string
}

export interface TestRunDetail extends TestRun {
  results: TestResult[]
}

export interface Environment {
  id: string
  name: string
  base_url: string
}

export interface Browser {
  id: string
  name: string
  version?: string
}

export interface TestRunFilters {
  status?: string
  dateFrom?: string
  dateTo?: string
  page: number
  limit: number
}

interface TestRunsState {
  // Data
  runs: TestRun[]
  currentRun: TestRunDetail | null
  environments: Environment[]
  browsers: Browser[]

  // UI State
  loading: boolean
  loadingRun: boolean
  creating: boolean
  error: string | null

  // Filters & Pagination
  filters: TestRunFilters
  totalCount: number

  // Actions
  fetchRuns: () => Promise<void>
  fetchRun: (id: string) => Promise<void>
  createRun: (data: {
    environment: string
    scenario_tags?: string[]
    scenario_ids?: string[]
    browsers?: string[]
  }) => Promise<TestRun>
  fetchEnvironments: () => Promise<void>
  fetchBrowsers: () => Promise<void>
  setFilters: (filters: Partial<TestRunFilters>) => void
  resetFilters: () => void
  clearCurrentRun: () => void
  clearError: () => void
}

const defaultFilters: TestRunFilters = {
  status: undefined,
  dateFrom: undefined,
  dateTo: undefined,
  page: 1,
  limit: 10,
}

export const useTestRunsStore = create<TestRunsState>((set, get) => ({
  // Initial state
  runs: [],
  currentRun: null,
  environments: [],
  browsers: [],
  loading: false,
  loadingRun: false,
  creating: false,
  error: null,
  filters: { ...defaultFilters },
  totalCount: 0,

  // Actions
  fetchRuns: async () => {
    set({ loading: true, error: null })
    try {
      const { filters } = get()
      const params: Record<string, unknown> = {
        limit: filters.limit,
        offset: (filters.page - 1) * filters.limit,
      }
      if (filters.status) params.status = filters.status
      if (filters.dateFrom) params.date_from = filters.dateFrom
      if (filters.dateTo) params.date_to = filters.dateTo

      const data = await getTestRuns(params as { status?: string; limit?: number })
      set({ runs: Array.isArray(data) ? data : data.items || [], totalCount: data.total || data.length || 0 })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch test runs'
      set({ error: message })
    } finally {
      set({ loading: false })
    }
  },

  fetchRun: async (id: string) => {
    set({ loadingRun: true, error: null })
    try {
      const data = await getTestRun(id)
      set({ currentRun: data })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch test run'
      set({ error: message })
    } finally {
      set({ loadingRun: false })
    }
  },

  createRun: async (data) => {
    set({ creating: true, error: null })
    try {
      const run = await createTestRun(data)
      set((state) => ({ runs: [run, ...state.runs] }))
      return run
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create test run'
      set({ error: message })
      throw error
    } finally {
      set({ creating: false })
    }
  },

  fetchEnvironments: async () => {
    try {
      const data = await getEnvironments()
      set({ environments: Array.isArray(data) ? data : data.items || [] })
    } catch (error) {
      console.error('Failed to fetch environments:', error)
    }
  },

  fetchBrowsers: async () => {
    try {
      const data = await getBrowsers()
      set({ browsers: Array.isArray(data) ? data : data.items || [] })
    } catch (error) {
      // Fallback to default browsers if endpoint not available
      set({
        browsers: [
          { id: 'chromium', name: 'Chromium' },
          { id: 'firefox', name: 'Firefox' },
          { id: 'webkit', name: 'WebKit' },
        ]
      })
    }
  },

  setFilters: (newFilters) => {
    set((state) => ({
      filters: { ...state.filters, ...newFilters, page: newFilters.page ?? 1 }
    }))
  },

  resetFilters: () => {
    set({ filters: { ...defaultFilters } })
  },

  clearCurrentRun: () => {
    set({ currentRun: null })
  },

  clearError: () => {
    set({ error: null })
  },
}))
