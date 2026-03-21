/**
 * Hook for real-time test run updates via WebSocket.
 *
 * Connects to the backend WebSocket endpoint and provides real-time
 * status updates, step results, and progress information.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { getWebSocketUrl } from '../api/client'

// Message types received from the server
export type WebSocketMessageType =
  | 'connected'
  | 'status_update'
  | 'result_added'
  | 'progress'
  | 'completed'
  | 'error'

// Test result from WebSocket
export interface TestResult {
  id: string
  step_name: string
  status: 'passed' | 'failed' | 'skipped' | 'error' | 'pending'
  duration_ms: number
  error_message: string | null
  screenshot_url: string | null
}

// Progress data from WebSocket
export interface ProgressData {
  id: string
  status: string
  progress_message: string | null
  total_scenarios: number
  completed_steps: number
  passed: number
  failed: number
}

// Status update data from WebSocket
export interface StatusUpdateData {
  id: string
  old_status: string
  new_status: string
  started_at: string | null
  finished_at: string | null
}

// Completion data from WebSocket
export interface CompletedData {
  id: string
  status: string
  started_at: string | null
  finished_at: string | null
  total_results: number
  passed: number
  failed: number
  skipped: number
}

// Initial connection data
export interface ConnectedData {
  id: string
  status: string
  progress_message: string | null
  started_at: string | null
  finished_at: string | null
  total_scenarios: number
  results: TestResult[]
}

// WebSocket message structure
export interface WebSocketMessage {
  type: WebSocketMessageType
  data:
    | ConnectedData
    | StatusUpdateData
    | TestResult
    | ProgressData
    | CompletedData
    | { message: string }
}

// Connection state
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

// Hook return type
export interface UseTestRunWebSocketReturn {
  // Connection state
  connectionState: ConnectionState
  error: string | null

  // Run state
  status: string | null
  progressMessage: string | null
  startedAt: string | null
  finishedAt: string | null
  totalScenarios: number
  completedSteps: number
  passed: number
  failed: number
  skipped: number
  isComplete: boolean

  // Results
  results: TestResult[]

  // Actions
  reconnect: () => void
  disconnect: () => void
}

// Configuration options
export interface UseTestRunWebSocketOptions {
  /** Whether to auto-connect on mount (default: true) */
  autoConnect?: boolean
  /** Reconnect delay in ms (default: 2000) */
  reconnectDelay?: number
  /** Max reconnect attempts (default: 5) */
  maxReconnectAttempts?: number
  /** Ping interval in ms for keepalive (default: 30000) */
  pingInterval?: number
  /** Callback when status changes */
  onStatusChange?: (oldStatus: string, newStatus: string) => void
  /** Callback when a new result is added */
  onResultAdded?: (result: TestResult) => void
  /** Callback when run completes */
  onComplete?: (data: CompletedData) => void
  /** Callback on error */
  onError?: (message: string) => void
}

const COMPLETED_STATUSES = ['passed', 'failed', 'cancelled', 'error']

/**
 * Hook for subscribing to real-time test run updates via WebSocket.
 *
 * @param runId - The test run ID to subscribe to
 * @param options - Configuration options
 * @returns Real-time run state and control functions
 *
 * @example
 * ```tsx
 * const {
 *   connectionState,
 *   status,
 *   progressMessage,
 *   results,
 *   passed,
 *   failed,
 *   isComplete,
 * } = useTestRunWebSocket(runId, {
 *   onComplete: (data) => console.log('Run completed:', data.status),
 * })
 * ```
 */
export function useTestRunWebSocket(
  runId: string | null | undefined,
  options: UseTestRunWebSocketOptions = {}
): UseTestRunWebSocketReturn {
  const {
    autoConnect = true,
    reconnectDelay = 2000,
    maxReconnectAttempts = 5,
    pingInterval = 30000,
    onStatusChange,
    onResultAdded,
    onComplete,
    onError,
  } = options

  // Connection state
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [error, setError] = useState<string | null>(null)

  // Run state
  const [status, setStatus] = useState<string | null>(null)
  const [progressMessage, setProgressMessage] = useState<string | null>(null)
  const [startedAt, setStartedAt] = useState<string | null>(null)
  const [finishedAt, setFinishedAt] = useState<string | null>(null)
  const [totalScenarios, setTotalScenarios] = useState<number>(0)
  const [completedSteps, setCompletedSteps] = useState<number>(0)
  const [passed, setPassed] = useState<number>(0)
  const [failed, setFailed] = useState<number>(0)
  const [skipped, setSkipped] = useState<number>(0)
  const [results, setResults] = useState<TestResult[]>([])

  // Refs for WebSocket and reconnection
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef<number>(0)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Computed values
  const isComplete = status !== null && COMPLETED_STATUSES.includes(status)

  // Cleanup function
  const cleanup = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  // Disconnect function
  const disconnect = useCallback(() => {
    cleanup()
    setConnectionState('disconnected')
    reconnectAttemptsRef.current = maxReconnectAttempts // Prevent auto-reconnect
  }, [cleanup, maxReconnectAttempts])

  // Connect function
  const connect = useCallback(() => {
    if (!runId) return

    cleanup()
    setConnectionState('connecting')
    setError(null)

    const url = getWebSocketUrl(`/api/v1/ws/runs/${runId}`)
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnectionState('connected')
      setError(null)
      reconnectAttemptsRef.current = 0

      // Start ping interval for keepalive
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping')
        }
      }, pingInterval)
    }

    ws.onmessage = (event) => {
      // Handle pong responses
      if (event.data === 'pong') {
        return
      }

      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        handleMessage(message)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.onerror = () => {
      setConnectionState('error')
      setError('WebSocket connection error')
      onError?.('WebSocket connection error')
    }

    ws.onclose = (event) => {
      cleanup()

      // Don't reconnect if run is complete or was manually disconnected
      if (isComplete || reconnectAttemptsRef.current >= maxReconnectAttempts) {
        setConnectionState('disconnected')
        return
      }

      // Handle abnormal closure - try to reconnect
      if (event.code !== 1000 && event.code !== 4004) {
        setConnectionState('disconnected')
        reconnectAttemptsRef.current++

        const delay = reconnectDelay * Math.pow(2, reconnectAttemptsRef.current - 1)
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, Math.min(delay, 30000)) // Cap at 30 seconds
      } else {
        setConnectionState('disconnected')
      }
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId, pingInterval, reconnectDelay, maxReconnectAttempts, cleanup])

  // Handle incoming messages
  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      switch (message.type) {
        case 'connected': {
          const data = message.data as ConnectedData
          setStatus(data.status)
          setProgressMessage(data.progress_message)
          setStartedAt(data.started_at)
          setFinishedAt(data.finished_at)
          setTotalScenarios(data.total_scenarios)
          setResults(data.results || [])

          // Calculate counts from initial results
          const initialResults = data.results || []
          setPassed(initialResults.filter((r) => r.status === 'passed').length)
          setFailed(initialResults.filter((r) => r.status === 'failed').length)
          setSkipped(initialResults.filter((r) => r.status === 'skipped').length)
          setCompletedSteps(initialResults.length)
          break
        }

        case 'status_update': {
          const data = message.data as StatusUpdateData
          setStatus(data.new_status)
          setStartedAt(data.started_at)
          setFinishedAt(data.finished_at)
          onStatusChange?.(data.old_status, data.new_status)
          break
        }

        case 'result_added': {
          const result = message.data as TestResult
          setResults((prev) => [...prev, result])
          setCompletedSteps((prev) => prev + 1)

          if (result.status === 'passed') {
            setPassed((prev) => prev + 1)
          } else if (result.status === 'failed' || result.status === 'error') {
            setFailed((prev) => prev + 1)
          } else if (result.status === 'skipped') {
            setSkipped((prev) => prev + 1)
          }

          onResultAdded?.(result)
          break
        }

        case 'progress': {
          const data = message.data as ProgressData
          setStatus(data.status)
          setProgressMessage(data.progress_message)
          setTotalScenarios(data.total_scenarios)
          setCompletedSteps(data.completed_steps)
          setPassed(data.passed)
          setFailed(data.failed)
          break
        }

        case 'completed': {
          const data = message.data as CompletedData
          setStatus(data.status)
          setStartedAt(data.started_at)
          setFinishedAt(data.finished_at)
          setCompletedSteps(data.total_results)
          setPassed(data.passed)
          setFailed(data.failed)
          setSkipped(data.skipped)
          onComplete?.(data)

          // Close connection after completion
          if (wsRef.current) {
            wsRef.current.close(1000, 'Run completed')
          }
          break
        }

        case 'error': {
          const data = message.data as { message: string }
          setError(data.message)
          onError?.(data.message)
          break
        }
      }
    },
    [onStatusChange, onResultAdded, onComplete, onError]
  )

  // Reconnect function (exposed to caller)
  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0
    connect()
  }, [connect])

  // Auto-connect on mount and when runId changes
  useEffect(() => {
    if (autoConnect && runId) {
      connect()
    }

    return () => {
      cleanup()
    }
  }, [autoConnect, runId, connect, cleanup])

  return {
    connectionState,
    error,
    status,
    progressMessage,
    startedAt,
    finishedAt,
    totalScenarios,
    completedSteps,
    passed,
    failed,
    skipped,
    isComplete,
    results,
    reconnect,
    disconnect,
  }
}

export default useTestRunWebSocket
