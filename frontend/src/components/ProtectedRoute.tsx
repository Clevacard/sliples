import { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation()
  const { isAuthenticated, isLoading, user, fetchCurrentUser, setLoading } = useAuthStore()
  const [hasApiKey, setHasApiKey] = useState(false)

  // Check authentication on mount
  useEffect(() => {
    const apiKey = localStorage.getItem('sliples_api_key')
    setHasApiKey(!!apiKey)

    if (apiKey) {
      // API key auth - mark as ready without calling /auth/me
      setLoading(false)
    } else if (!user) {
      // No API key and no user - try to fetch current user from session
      fetchCurrentUser()
    } else {
      // Already have user
      setLoading(false)
    }
  }, [fetchCurrentUser, user, setLoading])

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4">
            <svg
              className="animate-spin w-full h-full text-primary-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  // Redirect to login if not authenticated (but allow if API key is present)
  if (!isAuthenticated && !hasApiKey) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
