/**
 * Custom React hooks for Sliples.
 */

export {
  useTestRunWebSocket,
  type UseTestRunWebSocketReturn,
  type UseTestRunWebSocketOptions,
  type WebSocketMessageType,
  type TestResult,
  type ProgressData,
  type StatusUpdateData,
  type CompletedData,
  type ConnectedData,
  type WebSocketMessage,
  type ConnectionState,
} from './useTestRunWebSocket'

export {
  usePlaybackWebSocket,
  type UsePlaybackWebSocketReturn,
  type UsePlaybackWebSocketOptions,
  type PlaybackStepResult,
  type PlaybackStatusData,
  type PlaybackCompletedData,
} from './usePlaybackWebSocket'
