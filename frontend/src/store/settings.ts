import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import * as api from '../api/client'

export interface ApiKey {
  id: string
  name: string
  key_prefix: string
  created_at: string
  last_used_at: string | null
}

export interface Preferences {
  theme: 'dark' | 'light'
  notifications: {
    emailOnFailure: boolean
    emailOnSuccess: boolean
    browserNotifications: boolean
  }
}

export interface SystemConfig {
  email?: {
    configured: boolean
    host?: string
    port?: number
    from_address?: string
    tls_enabled?: boolean
  }
  storage?: {
    configured: boolean
    endpoint?: string
    bucket?: string
    access_key?: string
    region?: string
  }
  retention?: {
    default_days: number
    cleanup_schedule?: string
    last_cleanup?: string
  }
}

interface SettingsState {
  // API Keys
  apiKeys: ApiKey[]
  isLoadingKeys: boolean
  isCreatingKey: boolean
  isRevokingKey: string | null  // ID of key being revoked
  keysError: string | null

  // System Configuration
  systemConfig: SystemConfig | null
  isLoadingConfig: boolean
  configError: string | null

  // Preferences
  preferences: Preferences

  // Actions
  fetchApiKeys: () => Promise<void>
  createApiKey: (name: string) => Promise<api.CreateApiKeyResponse>
  revokeApiKey: (id: string) => Promise<void>
  fetchSystemConfig: () => Promise<void>
  updatePreferences: (updates: Partial<Preferences>) => void
  clearKeysError: () => void
}

const defaultPreferences: Preferences = {
  theme: 'dark',
  notifications: {
    emailOnFailure: true,
    emailOnSuccess: false,
    browserNotifications: true,
  },
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      // Initial state
      apiKeys: [],
      isLoadingKeys: false,
      isCreatingKey: false,
      isRevokingKey: null,
      keysError: null,
      systemConfig: null,
      isLoadingConfig: false,
      configError: null,
      preferences: defaultPreferences,

      // Fetch API keys
      fetchApiKeys: async () => {
        set({ isLoadingKeys: true, keysError: null })
        try {
          const keys = await api.listApiKeys()
          set({ apiKeys: keys, isLoadingKeys: false })
        } catch (error) {
          console.error('Failed to fetch API keys:', error)
          set({
            keysError: error instanceof Error ? error.message : 'Failed to load API keys',
            isLoadingKeys: false,
          })
        }
      },

      // Create API key
      createApiKey: async (name: string) => {
        set({ isCreatingKey: true, keysError: null })
        try {
          const response = await api.createApiKey(name)
          // Refresh the list to include the new key (without the full key)
          await get().fetchApiKeys()
          set({ isCreatingKey: false })
          return response
        } catch (error) {
          console.error('Failed to create API key:', error)
          set({
            keysError: error instanceof Error ? error.message : 'Failed to create API key',
            isCreatingKey: false,
          })
          throw error
        }
      },

      // Revoke API key
      revokeApiKey: async (id: string) => {
        set({ isRevokingKey: id, keysError: null })
        try {
          await api.revokeApiKey(id)
          // Remove from local state
          set((state) => ({
            apiKeys: state.apiKeys.filter((key) => key.id !== id),
            isRevokingKey: null,
          }))
        } catch (error) {
          console.error('Failed to revoke API key:', error)
          set({
            keysError: error instanceof Error ? error.message : 'Failed to revoke API key',
            isRevokingKey: null,
          })
          throw error
        }
      },

      // Fetch system configuration
      fetchSystemConfig: async () => {
        set({ isLoadingConfig: true, configError: null })
        try {
          const config = await api.getSystemConfig()
          set({ systemConfig: config, isLoadingConfig: false })
        } catch (error) {
          console.error('Failed to fetch system config:', error)
          set({
            configError: error instanceof Error ? error.message : 'Failed to load system configuration',
            isLoadingConfig: false,
          })
        }
      },

      // Update preferences
      updatePreferences: (updates: Partial<Preferences>) => {
        set((state) => ({
          preferences: {
            ...state.preferences,
            ...updates,
            notifications: {
              ...state.preferences.notifications,
              ...(updates.notifications || {}),
            },
          },
        }))
      },

      // Clear error
      clearKeysError: () => set({ keysError: null }),
    }),
    {
      name: 'sliples-settings',
      partialize: (state) => ({
        preferences: state.preferences,
      }),
    }
  )
)
