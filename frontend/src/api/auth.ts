import { api } from './client'
import type { User } from '../store/auth'

const API_URL = import.meta.env.VITE_API_URL || ''

/**
 * Get the Google OAuth authorization URL
 */
export function getGoogleAuthUrl(): string {
  return `${API_URL}/api/v1/auth/google/login`
}

/**
 * Exchange OAuth code for session
 */
export async function handleOAuthCallback(code: string): Promise<User> {
  const response = await api.post('/auth/google/callback', { code })
  return response.data.user
}

/**
 * Get the current authenticated user
 */
export async function getCurrentUser(): Promise<User> {
  const response = await api.get('/auth/me')
  return response.data
}

/**
 * Logout the current user
 */
export async function logout(): Promise<void> {
  await api.post('/auth/logout')
}
