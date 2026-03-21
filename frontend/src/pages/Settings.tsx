import { useState, useEffect } from 'react'
import { useAuthStore } from '../store/auth'
import { useSettingsStore } from '../store/settings'
import ApiKeyManager from '../components/ApiKeyManager'

type TabId = 'profile' | 'apikeys' | 'system' | 'preferences'

interface Tab {
  id: TabId
  name: string
  icon: React.ReactNode
}

const tabs: Tab[] = [
  {
    id: 'profile',
    name: 'Profile',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
  },
  {
    id: 'apikeys',
    name: 'API Keys',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
      </svg>
    ),
  },
  {
    id: 'system',
    name: 'System',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
      </svg>
    ),
  },
  {
    id: 'preferences',
    name: 'Preferences',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
]

function ProfileTab() {
  const { user } = useAuthStore()

  return (
    <div className="space-y-6">
      {/* User Info Card */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-100 mb-6">User Information</h3>

        <div className="flex items-start gap-6">
          {/* Avatar */}
          <div className="flex-shrink-0">
            {user?.picture_url ? (
              <img
                src={user.picture_url}
                alt={user.name}
                className="w-20 h-20 rounded-full border-2 border-gray-700"
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-gray-700 flex items-center justify-center">
                <span className="text-2xl font-medium text-gray-400">
                  {user?.name?.charAt(0).toUpperCase() || '?'}
                </span>
              </div>
            )}
          </div>

          {/* User Details */}
          <div className="flex-1 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Name</label>
              <p className="text-gray-100">{user?.name || 'Not available'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
              <p className="text-gray-100">{user?.email || 'Not available'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Role</label>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                user?.role === 'admin'
                  ? 'bg-purple-500/20 text-purple-400'
                  : user?.role === 'user'
                  ? 'bg-blue-500/20 text-blue-400'
                  : 'bg-gray-500/20 text-gray-400'
              }`}>
                {user?.role || 'viewer'}
              </span>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-700">
          <p className="text-sm text-gray-500">
            Profile information is managed through your SSO provider (Google).
            To update your information, please update it in your Google account.
          </p>
        </div>
      </div>

      {/* About Section */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-100 mb-4">About Sliples</h3>
        <div className="text-sm text-gray-400 space-y-2">
          <p>
            <span className="text-gray-500">Version:</span>{' '}
            <span className="text-gray-300">0.1.0</span>
          </p>
          <p className="pt-2 text-gray-400">
            Sliples allows you to write test scenarios in plain English (Gherkin),
            execute them across multiple browsers, and integrate with CI/CD pipelines.
          </p>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-700 space-y-2">
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-blue-400 hover:text-blue-300 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            API Documentation (Swagger)
          </a>
          <a
            href="/api/v1/health"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-blue-400 hover:text-blue-300 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Health Check Endpoint
          </a>
        </div>
      </div>
    </div>
  )
}

function SystemTab() {
  const {
    systemConfig,
    isLoadingConfig,
    configError,
    fetchSystemConfig,
  } = useSettingsStore()

  useEffect(() => {
    fetchSystemConfig()
  }, [fetchSystemConfig])

  if (isLoadingConfig) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="card">
          <div className="h-6 bg-gray-700 rounded w-40 mb-4" />
          <div className="space-y-3">
            <div className="h-4 bg-gray-700 rounded w-full" />
            <div className="h-4 bg-gray-700 rounded w-3/4" />
            <div className="h-4 bg-gray-700 rounded w-1/2" />
          </div>
        </div>
        <div className="card">
          <div className="h-6 bg-gray-700 rounded w-48 mb-4" />
          <div className="space-y-3">
            <div className="h-4 bg-gray-700 rounded w-full" />
            <div className="h-4 bg-gray-700 rounded w-2/3" />
          </div>
        </div>
      </div>
    )
  }

  if (configError) {
    return (
      <div className="card border-red-500/30 bg-red-500/10">
        <div className="flex items-center gap-3">
          <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-red-400 font-medium">Failed to load system configuration</p>
            <p className="text-red-400/70 text-sm mt-1">{configError}</p>
          </div>
        </div>
        <button
          onClick={() => fetchSystemConfig()}
          className="mt-4 btn btn-secondary text-sm"
        >
          Retry
        </button>
      </div>
    )
  }

  const maskValue = (value: string | undefined, showChars: number = 4): string => {
    if (!value) return 'Not configured'
    if (value.length <= showChars * 2) return '*'.repeat(value.length)
    return value.substring(0, showChars) + '*'.repeat(8) + value.substring(value.length - showChars)
  }

  return (
    <div className="space-y-6">
      {/* Email Configuration */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-100">Email Configuration</h3>
            <p className="text-sm text-gray-400">SMTP settings for email notifications</p>
          </div>
          <span className={`ml-auto px-2.5 py-0.5 rounded-full text-xs font-medium ${
            systemConfig?.email?.configured
              ? 'bg-green-500/20 text-green-400'
              : 'bg-yellow-500/20 text-yellow-400'
          }`}>
            {systemConfig?.email?.configured ? 'Configured' : 'Not Configured'}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">SMTP Host</label>
            <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-gray-300 font-mono text-sm">
              {systemConfig?.email?.host || 'Not configured'}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">SMTP Port</label>
            <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-gray-300 font-mono text-sm">
              {systemConfig?.email?.port || 'Not configured'}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">From Address</label>
            <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-gray-300 font-mono text-sm">
              {systemConfig?.email?.from_address || 'Not configured'}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">TLS Enabled</label>
            <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-gray-300 font-mono text-sm">
              {systemConfig?.email?.tls_enabled !== undefined
                ? (systemConfig.email.tls_enabled ? 'Yes' : 'No')
                : 'Not configured'}
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-700">
          <p className="text-xs text-gray-500">
            Email settings are configured via environment variables. Contact your administrator to modify these settings.
          </p>
        </div>
      </div>

      {/* Storage Configuration */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-100">Storage Configuration</h3>
            <p className="text-sm text-gray-400">S3/MinIO settings for screenshots and artifacts</p>
          </div>
          <span className={`ml-auto px-2.5 py-0.5 rounded-full text-xs font-medium ${
            systemConfig?.storage?.configured
              ? 'bg-green-500/20 text-green-400'
              : 'bg-yellow-500/20 text-yellow-400'
          }`}>
            {systemConfig?.storage?.configured ? 'Configured' : 'Not Configured'}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Endpoint</label>
            <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-gray-300 font-mono text-sm truncate">
              {systemConfig?.storage?.endpoint || 'Not configured'}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Bucket</label>
            <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-gray-300 font-mono text-sm">
              {systemConfig?.storage?.bucket || 'Not configured'}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Access Key</label>
            <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-gray-300 font-mono text-sm">
              {maskValue(systemConfig?.storage?.access_key)}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Region</label>
            <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-gray-300 font-mono text-sm">
              {systemConfig?.storage?.region || 'Not configured'}
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-700">
          <p className="text-xs text-gray-500">
            Storage settings are configured via environment variables. Contact your administrator to modify these settings.
          </p>
        </div>
      </div>

      {/* Data Retention */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-orange-500/20 rounded-lg">
            <svg className="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-100">Data Retention</h3>
            <p className="text-sm text-gray-400">Automatic cleanup policy for test data</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Default Retention Period</label>
            <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-gray-300 font-mono text-sm">
              {systemConfig?.retention?.default_days
                ? `${systemConfig.retention.default_days} days`
                : '365 days (default)'}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Cleanup Schedule</label>
            <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-gray-300 font-mono text-sm">
              {systemConfig?.retention?.cleanup_schedule || 'Daily at midnight'}
            </div>
          </div>
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-400 mb-1">Last Cleanup Run</label>
            <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-gray-300 font-mono text-sm">
              {systemConfig?.retention?.last_cleanup
                ? new Date(systemConfig.retention.last_cleanup).toLocaleString()
                : 'Never'}
            </div>
          </div>
        </div>

        <div className="mt-4 p-4 bg-gray-700/30 rounded-lg">
          <h4 className="text-sm font-medium text-gray-300 mb-2">What gets deleted?</h4>
          <ul className="text-sm text-gray-400 space-y-1">
            <li className="flex items-center gap-2">
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Test run results older than retention period
            </li>
            <li className="flex items-center gap-2">
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Screenshots and artifacts from deleted runs
            </li>
            <li className="flex items-center gap-2">
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Log files older than retention period
            </li>
          </ul>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-700">
          <p className="text-xs text-gray-500">
            Per-environment retention can be configured in the Environments settings. The system default is 12 months (365 days).
          </p>
        </div>
      </div>
    </div>
  )
}

function PreferencesTab() {
  const { preferences, updatePreferences } = useSettingsStore()

  const handleThemeChange = (theme: 'dark' | 'light') => {
    updatePreferences({ theme })
    // In the future, this would also update the actual theme
    // For now, the app is dark theme only
  }

  const handleNotificationChange = (key: keyof typeof preferences.notifications, value: boolean) => {
    updatePreferences({
      notifications: {
        ...preferences.notifications,
        [key]: value,
      },
    })
  }

  return (
    <div className="space-y-6">
      {/* Theme Settings */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Appearance</h3>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-3">Theme</label>
          <div className="flex gap-3">
            <button
              onClick={() => handleThemeChange('dark')}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                preferences.theme === 'dark'
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-gray-700 bg-gray-800 hover:border-gray-600'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <svg className="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
                <span className="text-gray-200 font-medium">Dark</span>
              </div>
            </button>
            <button
              onClick={() => handleThemeChange('light')}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                preferences.theme === 'light'
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-gray-700 bg-gray-800 hover:border-gray-600'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <svg className="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                <span className="text-gray-200 font-medium">Light</span>
              </div>
            </button>
          </div>
          {preferences.theme === 'light' && (
            <p className="text-xs text-yellow-500 mt-2">
              Light theme is coming soon. Currently using dark theme.
            </p>
          )}
        </div>
      </div>

      {/* Notification Settings */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Notifications</h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-200 font-medium">Email on failure</p>
              <p className="text-sm text-gray-500">Receive an email when a test run fails</p>
            </div>
            <button
              onClick={() => handleNotificationChange('emailOnFailure', !preferences.notifications.emailOnFailure)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                preferences.notifications.emailOnFailure ? 'bg-blue-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.notifications.emailOnFailure ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-200 font-medium">Email on success</p>
              <p className="text-sm text-gray-500">Receive an email when a test run passes</p>
            </div>
            <button
              onClick={() => handleNotificationChange('emailOnSuccess', !preferences.notifications.emailOnSuccess)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                preferences.notifications.emailOnSuccess ? 'bg-blue-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.notifications.emailOnSuccess ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-200 font-medium">Browser notifications</p>
              <p className="text-sm text-gray-500">Show desktop notifications for test run status</p>
            </div>
            <button
              onClick={() => handleNotificationChange('browserNotifications', !preferences.notifications.browserNotifications)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                preferences.notifications.browserNotifications ? 'bg-blue-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.notifications.browserNotifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Data & Privacy */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Data & Privacy</h3>
        <p className="text-sm text-gray-400 mb-4">
          Your preferences are stored locally in your browser. Test data and API keys are stored securely on the server.
        </p>
        <p className="text-sm text-gray-500">
          Test data is automatically deleted after 12 months according to the retention policy.
        </p>
      </div>
    </div>
  )
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState<TabId>('profile')

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-100 mb-8">Settings</h1>

      {/* Tab Navigation */}
      <div className="flex gap-1 p-1 bg-gray-800 rounded-lg mb-8 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-gray-700 text-gray-100'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'
            }`}
          >
            {tab.icon}
            {tab.name}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'profile' && <ProfileTab />}
        {activeTab === 'apikeys' && <ApiKeyManager />}
        {activeTab === 'system' && <SystemTab />}
        {activeTab === 'preferences' && <PreferencesTab />}
      </div>
    </div>
  )
}
