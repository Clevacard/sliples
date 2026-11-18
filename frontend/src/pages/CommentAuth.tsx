import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuthStore } from '../store/auth'

/**
 * Comment auth tab (recorder comments, design §2 / §6.4).
 *
 * The recorder snippet opens /comment-auth/{nonce} in a NEW tab after the
 * comment hotkey. This page completes the device-flow: it requires an
 * authenticated session cookie, calls comment-auth complete, and then tells the
 * user to close the tab. The original (recorded) window polls the nonce and
 * receives the scoped 4h comment token.
 *
 * This route is PUBLIC (no Layout/ProtectedRoute) so the OAuth round-trip can
 * return here: unauthenticated users are sent to /login?from=/comment-auth/{nonce}
 * and AuthCallback restores this path after Google sign-in.
 */
export default function CommentAuth() {
  const { nonce } = useParams<{ nonce: string }>()
  const navigate = useNavigate()
  const { isAuthenticated, isLoading, fetchCurrentUser } = useAuthStore()
  const [status, setStatus] = useState<'loading' | 'done' | 'error'>('loading')
  const [errorMsg, setErrorMsg] = useState<string>('')

  useEffect(() => {
    // Always validate the session cookie with the server on mount.
    fetchCurrentUser()
  }, [fetchCurrentUser])

  useEffect(() => {
    if (isLoading) return
    if (!nonce) {
      setStatus('error')
      setErrorMsg('This comment link is invalid (missing token). Please trigger the comment hotkey again.')
      return
    }
    if (!isAuthenticated) {
      // Send through SSO; AuthCallback returns here afterwards.
      navigate(`/login?from=${encodeURIComponent(`/comment-auth/${nonce}`)}`, { replace: true })
      return
    }
    // Authenticated: complete the comment-auth flow.
    const complete = async () => {
      try {
        await api.post(`/recorder/comment-auth/${nonce}/complete`)
        setStatus('done')
      } catch (err: any) {
        const code = err?.response?.status
        if (code === 404) {
          setErrorMsg('This comment link has expired. Go back to the recorded page and press the comment hotkey again.')
        } else if (code === 409) {
          setErrorMsg('This comment link was already used. Go back to the recorded page to continue.')
        } else {
          setErrorMsg(err?.message || 'Failed to authorise commenting. Please try again.')
        }
        setStatus('error')
      }
    }
    complete()
  }, [isAuthenticated, isLoading, nonce, navigate])

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md bg-gray-800 rounded-lg shadow-xl p-8 text-center">
        {status === 'loading' && (
          <>
            <div className="w-16 h-16 mx-auto mb-4">
              <svg className="animate-spin w-full h-full text-primary-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Authorising commenting…</h2>
            <p className="text-gray-400">Linking your account to the recorded session.</p>
          </>
        )}
        {status === 'done' && (
          <>
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-900/50 flex items-center justify-center">
              <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">You're all set</h2>
            <p className="text-gray-400">You can close this tab and return to the recorded page to add your comment.</p>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-900/50 flex items-center justify-center">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Something went wrong</h2>
            <p className="text-gray-400 mb-6">{errorMsg}</p>
            <button
              onClick={() => window.close()}
              className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
            >
              Close this tab
            </button>
          </>
        )}
      </div>
    </div>
  )
}
