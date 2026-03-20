import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies for session auth
})

// Add API key to requests
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('sliples_api_key')
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey
  }
  return config
})

// Health check
export async function checkHealth() {
  const response = await api.get('/health')
  return response.data
}

// Environments
export async function getEnvironments() {
  const response = await api.get('/environments')
  return response.data
}

export async function createEnvironment(data: {
  name: string
  base_url: string
  variables?: Record<string, string>
}) {
  const response = await api.post('/environments', data)
  return response.data
}

// Scenarios
export async function getScenarios(params?: { tag?: string; repo_id?: string }) {
  const response = await api.get('/scenarios', { params })
  return response.data
}

export async function getScenario(id: string) {
  const response = await api.get(`/scenarios/${id}`)
  return response.data
}

// Test Runs
export async function getTestRuns(params?: { status?: string; limit?: number }) {
  const response = await api.get('/runs', { params })
  return response.data
}

export async function getTestRun(id: string) {
  const response = await api.get(`/runs/${id}`)
  return response.data
}

export async function createTestRun(data: {
  scenario_tags?: string[]
  scenario_ids?: string[]
  environment: string
  browsers?: string[]
}) {
  const response = await api.post('/runs', data)
  return response.data
}

// Repos
export async function getRepos() {
  const response = await api.get('/repos')
  return response.data
}

export async function createRepo(data: {
  name: string
  git_url: string
  branch?: string
}) {
  const response = await api.post('/repos', data)
  return response.data
}

export async function syncRepo(id: string) {
  const response = await api.post(`/repos/${id}/sync`)
  return response.data
}

// Browsers
export async function getBrowsers() {
  const response = await api.get('/browsers')
  return response.data
}

// Dashboard Stats
export interface DashboardStats {
  totalScenarios: number
  passRate: number
  last24hRuns: number
  failedTests: number
  trendData: { date: string; passed: number; failed: number }[]
}

export async function getDashboardStats(): Promise<DashboardStats> {
  // Aggregate stats from runs and scenarios
  const [runs, scenarios] = await Promise.all([
    getTestRuns({ limit: 100 }),
    getScenarios(),
  ])

  const now = new Date()
  const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000)
  const last7Days = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)

  // Calculate stats
  const passedRuns = runs.filter((r: { status: string }) => r.status === 'passed').length
  const failedRuns = runs.filter((r: { status: string }) => r.status === 'failed').length
  const passRate = runs.length > 0 ? Math.round((passedRuns / runs.length) * 100) : 0

  const last24hRunsCount = runs.filter(
    (r: { created_at: string }) => new Date(r.created_at) > last24h
  ).length

  // Build 7-day trend data
  const trendData: { date: string; passed: number; failed: number }[] = []
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    const dateStr = date.toISOString().split('T')[0]
    const dayStart = new Date(dateStr)
    const dayEnd = new Date(dayStart.getTime() + 24 * 60 * 60 * 1000)

    const dayRuns = runs.filter((r: { created_at: string }) => {
      const runDate = new Date(r.created_at)
      return runDate >= dayStart && runDate < dayEnd
    })

    trendData.push({
      date: dateStr,
      passed: dayRuns.filter((r: { status: string }) => r.status === 'passed').length,
      failed: dayRuns.filter((r: { status: string }) => r.status === 'failed').length,
    })
  }

  return {
    totalScenarios: scenarios.length,
    passRate,
    last24hRuns: last24hRunsCount,
    failedTests: failedRuns,
    trendData,
  }
}

// Delete Repo
export async function deleteRepo(id: string) {
  const response = await api.delete(`/repos/${id}`)
  return response.data
}

// Get Repo Details
export async function getRepoDetails(id: string) {
  const response = await api.get(`/repos/${id}`)
  return response.data
}

// Sync all repos
export async function syncAllRepos() {
  const repos = await getRepos()
  return Promise.all(repos.map((repo: { id: string }) => syncRepo(repo.id)))
}
