import { create } from 'zustand'
import { getDashboardStats, getTestRuns, getRepos, syncAllRepos, createTestRun, DashboardStats } from '../api/client'

export interface TestRun {
  id: string
  status: 'pending' | 'running' | 'passed' | 'failed'
  browser: string
  created_at: string
  finished_at?: string
  environment?: string
  scenario_count?: number
  passed_count?: number
  failed_count?: number
}

export interface Repo {
  id: string
  project_id?: string
  name: string
  git_url: string
  branch: string
  sync_path: string
  last_synced?: string
  scenario_count?: number
}

interface DashboardState {
  // Data
  stats: DashboardStats | null
  recentRuns: TestRun[]
  repos: Repo[]

  // Loading states
  isLoading: boolean
  isLoadingStats: boolean
  isRunningAllTests: boolean
  isSyncingRepos: boolean

  // Error states
  error: string | null

  // Actions
  fetchDashboardData: () => Promise<void>
  fetchStats: () => Promise<void>
  runAllTests: (environment: string) => Promise<void>
  syncAllRepositories: () => Promise<void>
  refreshRecentRuns: () => Promise<void>
  clearError: () => void
}

export const useDashboardStore = create<DashboardState>((set) => ({
  // Initial state
  stats: null,
  recentRuns: [],
  repos: [],
  isLoading: true,
  isLoadingStats: false,
  isRunningAllTests: false,
  isSyncingRepos: false,
  error: null,

  // Fetch all dashboard data
  fetchDashboardData: async () => {
    set({ isLoading: true, error: null, stats: null, recentRuns: [], repos: [] })
    try {
      const [stats, runs, repos] = await Promise.all([
        getDashboardStats(),
        getTestRuns({ limit: 10 }),
        getRepos(),
      ])
      set({
        stats,
        recentRuns: runs,
        repos,
        isLoading: false,
      })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      set({
        error: 'Failed to load dashboard data. Please try again.',
        isLoading: false,
      })
    }
  },

  // Fetch only stats (for refresh)
  fetchStats: async () => {
    set({ isLoadingStats: true })
    try {
      const stats = await getDashboardStats()
      set({ stats, isLoadingStats: false })
    } catch (error) {
      console.error('Failed to fetch stats:', error)
      set({ isLoadingStats: false })
    }
  },

  // Run all tests
  runAllTests: async (environment: string) => {
    set({ isRunningAllTests: true, error: null })
    try {
      // Empty scenario_tags triggers "run all scenarios" in the backend
      await createTestRun({
        environment,
        scenario_tags: [],
      })
      // Refresh recent runs after starting
      const runs = await getTestRuns({ limit: 10 })
      set({ recentRuns: runs, isRunningAllTests: false })
    } catch (error) {
      console.error('Failed to run all tests:', error)
      set({
        error: 'Failed to start test run. Please try again.',
        isRunningAllTests: false,
      })
    }
  },

  // Sync all repositories
  syncAllRepositories: async () => {
    set({ isSyncingRepos: true, error: null })
    try {
      await syncAllRepos()
      // Refresh repos and stats after sync
      const [repos, stats] = await Promise.all([
        getRepos(),
        getDashboardStats(),
      ])
      set({ repos, stats, isSyncingRepos: false })
    } catch (error) {
      console.error('Failed to sync repos:', error)
      set({
        error: 'Failed to sync repositories. Please try again.',
        isSyncingRepos: false,
      })
    }
  },

  // Refresh recent runs
  refreshRecentRuns: async () => {
    try {
      const runs = await getTestRuns({ limit: 10 })
      set({ recentRuns: runs })
    } catch (error) {
      console.error('Failed to refresh runs:', error)
    }
  },

  // Clear error
  clearError: () => set({ error: null }),
}))
