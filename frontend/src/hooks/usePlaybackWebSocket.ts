/**
 * Hook for real-time playback updates via WebSocket.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { getWebSocketUrl } from '../api/client'

export interface PlaybackStepResult {
  step_number: number
  event_type: string
  element: string
  status: 'passed' | 'failed'
  duration_ms: number
  error_message: string | null
}

export interface PlaybackStatusData {
  id: string
  status: string
  progress_message: string
  total_steps: number
  current_step: number
  passed: number
  failed: number
}

export interface PlaybackCompletedData {
  id: string
  status: string
  total_steps: number
  passed: number
  failed: number
  duration_ms: number
}

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface UsePlaybackWebSocketReturn {
  connectionState: ConnectionState
  error: string | null
  status: string | null
  progressMessage: string | null
  totalSteps: number
  currentStep: number
  passed: number
  failed: number
  isComplete: boolean
  stepResults: PlaybackStepResult[]
  reconnect: () => void
  disconnect: () => void
}

export interface UsePlaybackWebSocketOptions {
  autoConnect?: boolean
  onStepResult?: (result: PlaybackStepResult) => void
  onComplete?: (data: PlaybackCompletedData) => void
  onError?: (message: string) => void
}

const COMPLETED_STATUSES = ['passed', 'failed']

export function usePlaybackWebSocket(
  playbackId: string | null | undefined,
  options: UsePlaybackWebSocketOptions = {}
): UsePlaybackWebSocketReturn {
  const { autoConnect = true, onStepResult, onComplete, onError } = options

  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [progressMessage, setProgressMessage] = useState<string | null>(null)
  const [totalSteps, setTotalSteps] = useState<number>(0)
  const [currentStep, setCurrentStep] = useState<number>(0)
  const [passed, setPassed] = useState<number>(0)
  const [failed, setFailed] = useState<number>(0)
  const [stepResults, setStepResults] = useState<PlaybackStepResult[]>([])

  const wsRef = useRef<WebSocket | null>(null)
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const isComplete = status !== null && COMPLETED_STATUSES.includes(status)

  const cleanup = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const disconnect = useCallback(() => {
    cleanup()
    setConnectionState('disconnected')
  }, [cleanup])

  const connect = useCallback(() => {
    if (!playbackId) return

    cleanup()
    setConnectionState('connecting')
    setError(null)
    setStepResults([])

    const url = getWebSocketUrl(`/api/v1/ws/playback/${playbackId}`)
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnectionState('connected')
      setError(null)

      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping')
        }
      }, 30000)
    }

    ws.onmessage = (event) => {
      if (event.data === 'pong') return

      try {
        const message = JSON.parse(event.data)
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

    ws.onclose = () => {
      cleanup()
      setConnectionState('disconnected')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playbackId, cleanup])

  const handleMessage = useCallback(
    (message: { type: string; data: any }) => {
      switch (message.type) {
        case 'connected': {
          const data = message.data as PlaybackStatusData
          setStatus(data.status)
          setProgressMessage(data.progress_message)
          setTotalSteps(data.total_steps)
          setCurrentStep(data.current_step || 0)
          setPassed(data.passed)
          setFailed(data.failed)
          break
        }

        case 'status': {
          const data = message.data as PlaybackStatusData
          setStatus(data.status)
          setProgressMessage(data.progress_message)
          setTotalSteps(data.total_steps)
          setCurrentStep(data.current_step)
          setPassed(data.passed)
          setFailed(data.failed)
          break
        }

        case 'step_result': {
          const result = message.data as PlaybackStepResult
          setStepResults((prev) => [...prev, result])
          onStepResult?.(result)
          break
        }

        case 'completed': {
          const data = message.data as PlaybackCompletedData
          setStatus(data.status)
          setTotalSteps(data.total_steps)
          setPassed(data.passed)
          setFailed(data.failed)
          onComplete?.(data)

          if (wsRef.current) {
            wsRef.current.close(1000, 'Playback completed')
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
    [onStepResult, onComplete, onError]
  )

  const reconnect = useCallback(() => {
    connect()
  }, [connect])

  useEffect(() => {
    if (autoConnect && playbackId) {
      connect()
    }
    return () => cleanup()
  }, [autoConnect, playbackId, connect, cleanup])

  return {
    connectionState,
    error,
    status,
    progressMessage,
    totalSteps,
    currentStep,
    passed,
    failed,
    isComplete,
    stepResults,
    reconnect,
    disconnect,
  }
}

export default usePlaybackWebSocket
