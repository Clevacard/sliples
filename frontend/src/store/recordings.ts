import { create } from 'zustand'
import {
  getRecordingSessions,
  getRecordingSession,
  getRecordingEvents,
  getRecordingComments,
  updateEventMetadata,
  deleteRecordingSession,
  RecordingSession,
  RecordedEvent,
  RecordingComment,
  EventMetadataUpdate,
} from '../api/client'

interface RecordingsState {
  sessions: RecordingSession[]
  currentSession: RecordingSession | null
  events: RecordedEvent[]
  comments: RecordingComment[]
  isLoading: boolean
  error: string | null

  fetchSessions: () => Promise<void>
  fetchSessionDetails: (sessionId: string) => Promise<void>
  fetchComments: (sessionId: string) => Promise<void>
  updateEvent: (sessionId: string, eventId: string, data: EventMetadataUpdate) => Promise<void>
  deleteSession: (sessionId: string) => Promise<void>
  clearError: () => void
}

export const useRecordingsStore = create<RecordingsState>()((set) => ({
  sessions: [],
  currentSession: null,
  events: [],
  comments: [],
  isLoading: true,
  error: null,

  fetchSessions: async () => {
    set({ isLoading: true, error: null })
    try {
      const sessions = await getRecordingSessions()
      set({ sessions })
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch recordings' })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchSessionDetails: async (sessionId: string) => {
    set({ isLoading: true, error: null })
    try {
      const [session, events, comments] = await Promise.all([
        getRecordingSession(sessionId),
        getRecordingEvents(sessionId),
        getRecordingComments(sessionId),
      ])
      set({ currentSession: session, events, comments })
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch session details' })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchComments: async (sessionId: string) => {
    try {
      const comments = await getRecordingComments(sessionId)
      set({ comments })
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch comments' })
    }
  },

  updateEvent: async (sessionId: string, eventId: string, data: EventMetadataUpdate) => {
    try {
      const updatedEvent = await updateEventMetadata(sessionId, eventId, data)
      // Update the events list
      set((state) => ({
        events: state.events.map((e) => (e.id === eventId ? updatedEvent : e)),
      }))
    } catch (error: any) {
      set({ error: error.message || 'Failed to update event' })
      throw error
    }
  },

  deleteSession: async (sessionId: string) => {
    try {
      await deleteRecordingSession(sessionId)
      // Remove from sessions list
      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId),
      }))
    } catch (error: any) {
      set({ error: error.message || 'Failed to delete session' })
      throw error
    }
  },

  clearError: () => set({ error: null }),
}))
