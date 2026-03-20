import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import * as authApi from '../api/auth'

export interface User {
  id: string
  email: string
  name: string
  picture_url: string | null
  role: 'admin' | 'user' | 'viewer'
}

interface AuthState {
  // State
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  login: () => void
  handleCallback: (code: string) => Promise<void>
  logout: () => Promise<void>
  fetchCurrentUser: () => Promise<void>
  clearError: () => void
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,

      // Redirect to Google OAuth
      login: () => {
        const authUrl = authApi.getGoogleAuthUrl()
        window.location.href = authUrl
      },

      // Handle OAuth callback
      handleCallback: async (code: string) => {
        set({ isLoading: true, error: null })
        try {
          const user = await authApi.handleOAuthCallback(code)
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error) {
          console.error('OAuth callback failed:', error)
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: error instanceof Error ? error.message : 'Authentication failed',
          })
          throw error
        }
      },

      // Logout
      logout: async () => {
        set({ isLoading: true })
        try {
          await authApi.logout()
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          })
        }
      },

      // Fetch current user (check session)
      fetchCurrentUser: async () => {
        const currentState = get()
        // If we already have a user from persisted state, just mark as not loading
        // This avoids clearing valid auth on temporary network/cookie issues
        if (currentState.user && currentState.isAuthenticated) {
          set({ isLoading: false })
          return
        }

        set({ isLoading: true })
        try {
          const user = await authApi.getCurrentUser()
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          // Not authenticated
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },

      // Clear error
      clearError: () => set({ error: null }),

      // Set loading state
      setLoading: (loading: boolean) => set({ isLoading: loading }),
    }),
    {
      name: 'sliples-auth',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
