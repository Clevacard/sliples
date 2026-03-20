import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../store/auth'

// Google logo SVG for the sign-in button
const GoogleLogo = () => (
  <svg
    className="w-5 h-5 mr-3"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      fill="#4285F4"
    />
    <path
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      fill="#34A853"
    />
    <path
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      fill="#FBBC05"
    />
    <path
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      fill="#EA4335"
    />
  </svg>
)

export default function Login() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { isAuthenticated, isLoading, error, login, clearError } = useAuthStore()

  const errorFromUrl = searchParams.get('error')
  const displayError = errorFromUrl || error

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate('/dashboard', { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate])

  // Clear error when component unmounts
  useEffect(() => {
    return () => clearError()
  }, [clearError])

  const handleGoogleSignIn = () => {
    login()
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center px-4">
      {/* Logo and title */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-primary-400 mb-2">Sliples</h1>
        <p className="text-gray-400">UI Automation Testing Platform</p>
      </div>

      {/* Login card */}
      <div className="w-full max-w-md bg-gray-800 rounded-lg shadow-xl p-8">
        <h2 className="text-2xl font-semibold text-white text-center mb-6">
          Sign in to your account
        </h2>

        {/* Error message */}
        {displayError && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg">
            <p className="text-red-300 text-sm text-center">
              {displayError === 'auth_failed'
                ? 'Authentication failed. Please try again.'
                : displayError === 'unauthorized'
                ? 'Your account is not authorized to access this application.'
                : displayError}
            </p>
          </div>
        )}

        {/* Google Sign In button */}
        <button
          onClick={handleGoogleSignIn}
          className="w-full flex items-center justify-center px-6 py-3 bg-white hover:bg-gray-100 text-gray-700 font-medium rounded-lg transition-colors shadow-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white"
        >
          <GoogleLogo />
          Sign in with Google
        </button>

        {/* Divider */}
        <div className="mt-6 flex items-center">
          <div className="flex-1 border-t border-gray-600"></div>
          <span className="px-4 text-gray-500 text-sm">Workspace SSO</span>
          <div className="flex-1 border-t border-gray-600"></div>
        </div>

        {/* Info text */}
        <p className="mt-6 text-center text-gray-500 text-sm">
          Sign in with your Google Workspace account to access Sliples.
        </p>
      </div>

      {/* Footer */}
      <p className="mt-8 text-gray-600 text-sm">
        Sliples v0.1.0
      </p>
    </div>
  )
}
