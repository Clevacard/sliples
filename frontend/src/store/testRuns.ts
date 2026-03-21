import { create } from 'zustand'
import { getTestRuns, getTestRun, createTestRun, retryTestRun, getEnvironments, getBrowsers, getWebSocketUrl } from '../api/client'

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
  progress_message?: string
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

// WebSocket message types
export interface WsStatusUpdate {
  type: 'status_update'
  data: {
    id: string
    old_status: string
    new_status: string
    started_at?: string
    finished_at?: string
  }
}

export interface WsResultAdded {
  type: 'result_added'
  data: TestResult
}

export interface WsProgress {
  type: 'progress'
  data: {
    id: string
    status: string
    progress_message?: string
    total_scenarios: number
    completed_steps: number
    passed: number
    failed: number
  }
}

export interface WsCompleted {
  type: 'completed'
  data: {
    id: string
    status: string
    started_at?: string
    finished_at?: string
    total_results: number
    passed: number
    failed: number
    skipped: number
  }
}

export interface WsError {
  type: 'error'
  data: {
    message: string
  }
}

export type WsMessage = WsStatusUpdate | WsResultAdded | WsProgress | WsCompleted | WsError

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

  // WebSocket state
  wsConnection: WebSocket | null
  wsConnected: boolean
  wsError: string | null

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
  retryRun: (id: string) => Promise<TestRun>
  fetchEnvironments: () => Promise<void>
  fetchBrowsers: () => Promise<void>
  setFilters: (filters: Partial<TestRunFilters>) => void
  resetFilters: () => void
  clearCurrentRun: () => void
  clearError: () => void

  // WebSocket actions
  connectWebSocket: (runId: string) => void
  disconnectWebSocket: () => void
  handleWsMessage: (message: WsMessage) => void
  updateRunFromWs: (data: Partial<TestRunDetail>) => void
  addResultFromWs: (result: TestResult) => void
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
  wsConnection: null,
  wsConnected: false,
  wsError: null,
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

  retryRun: async (id) => {
    set({ creating: true, error: null })
    try {
      const run = await retryTestRun(id)
      set((state) => ({ runs: [run, ...state.runs] }))
      return run
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to retry test run'
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

  // WebSocket actions
  connectWebSocket: (runId: string) => {
    const { wsConnection, disconnectWebSocket, handleWsMessage } = get()

    // Disconnect existing connection if any
    if (wsConnection) {
      disconnectWebSocket()
    }

    const wsUrl = getWebSocketUrl(`/api/v1/ws/runs/${runId}`)
    console.log('[WS] Connecting to:', wsUrl)

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('[WS] Connected')
      set({ wsConnected: true, wsError: null })
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WsMessage
        console.log('[WS] Message received:', message.type)
        handleWsMessage(message)
      } catch (e) {
        // Handle plain text messages like "pong"
        if (event.data === 'pong') {
          console.log('[WS] Pong received')
        }
      }
    }

    ws.onerror = (error) => {
      console.error('[WS] Error:', error)
      set({ wsError: 'WebSocket connection error' })
    }

    ws.onclose = (event) => {
      console.log('[WS] Disconnected:', event.code, event.reason)
      set({ wsConnection: null, wsConnected: false })
    }

    // Set up ping interval for keepalive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping')
      }
    }, 30000) // Ping every 30 seconds

    // Store cleanup function
    ;(ws as WebSocket & { _pingInterval?: ReturnType<typeof setInterval> })._pingInterval = pingInterval

    set({ wsConnection: ws })
  },

  disconnectWebSocket: () => {
    const { wsConnection } = get()
    if (wsConnection) {
      // Clear ping interval
      const wsWithInterval = wsConnection as WebSocket & { _pingInterval?: ReturnType<typeof setInterval> }
      if (wsWithInterval._pingInterval) {
        clearInterval(wsWithInterval._pingInterval)
      }
      wsConnection.close()
      set({ wsConnection: null, wsConnected: false })
    }
  },

  handleWsMessage: (message: WsMessage) => {
    const { currentRun, updateRunFromWs, addResultFromWs } = get()

    switch (message.type) {
      case 'status_update':
        if (currentRun && currentRun.id === message.data.id) {
          updateRunFromWs({
            status: message.data.new_status as TestRunDetail['status'],
            started_at: message.data.started_at,
            finished_at: message.data.finished_at,
          })
        }
        break

      case 'result_added':
        addResultFromWs(message.data)
        break

      case 'progress':
        if (currentRun && currentRun.id === message.data.id) {
          updateRunFromWs({
            status: message.data.status as TestRunDetail['status'],
            progress_message: message.data.progress_message,
          })
        }
        break

      case 'completed':
        if (currentRun && currentRun.id === message.data.id) {
          updateRunFromWs({
            status: message.data.status as TestRunDetail['status'],
            started_at: message.data.started_at,
            finished_at: message.data.finished_at,
          })
        }
        // Disconnect WebSocket after completion
        get().disconnectWebSocket()
        break

      case 'error':
        console.error('[WS] Server error:', message.data.message)
        set({ wsError: message.data.message })
        break
    }
  },

  updateRunFromWs: (data: Partial<TestRunDetail>) => {
    set((state) => {
      if (!state.currentRun) return state
      return {
        currentRun: { ...state.currentRun, ...data },
      }
    })
  },

  addResultFromWs: (result: TestResult) => {
    set((state) => {
      if (!state.currentRun) return state
      // Check if result already exists (avoid duplicates)
      const exists = state.currentRun.results.some((r) => r.id === result.id)
      if (exists) return state
      return {
        currentRun: {
          ...state.currentRun,
          results: [...state.currentRun.results, result],
        },
      }
    })
  },
}))
