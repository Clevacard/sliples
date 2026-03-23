import { create } from 'zustand'
import * as api from '../api/client'

export interface UserInfo {
  id: string
  email: string
  name: string
  picture_url: string | null
  workspace_domain: string
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
  last_login: string | null
}

interface UsersState {
  // State
  users: UserInfo[]
  isLoading: boolean
  error: string | null

  // Actions
  fetchUsers: (search?: string) => Promise<void>
  updateRole: (userId: string, role: 'admin' | 'user') => Promise<void>
  toggleActive: (userId: string, isActive: boolean) => Promise<void>
  clearError: () => void
}

export const useUsersStore = create<UsersState>()((set) => ({
  // Initial state
  users: [],
  isLoading: false,
  error: null,

  // Fetch all users
  fetchUsers: async (search?: string) => {
    set({ isLoading: true, error: null })
    try {
      const users = await api.listUsers(search)
      set({ users, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch users:', error)
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch users',
      })
    }
  },

  // Update user role
  updateRole: async (userId: string, role: 'admin' | 'user') => {
    set({ error: null })
    try {
      const updatedUser = await api.updateUserRole(userId, role)
      set((state) => ({
        users: state.users.map((u) =>
          u.id === userId ? { ...u, role: updatedUser.role as 'admin' | 'user' } : u
        ),
      }))
    } catch (error) {
      console.error('Failed to update user role:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to update role'
      set({ error: errorMessage })
      throw error
    }
  },

  // Toggle user active status
  toggleActive: async (userId: string, isActive: boolean) => {
    set({ error: null })
    try {
      const updatedUser = await api.toggleUserActive(userId, isActive)
      set((state) => ({
        users: state.users.map((u) =>
          u.id === userId ? { ...u, is_active: updatedUser.is_active } : u
        ),
      }))
    } catch (error) {
      console.error('Failed to toggle user active status:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to update status'
      set({ error: errorMessage })
      throw error
    }
  },

  // Clear error
  clearError: () => set({ error: null }),
}))
