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
export interface Environment {
  id: string
  name: string
  base_url: string
  credentials_env?: string
  variables: Record<string, string>
  retention_days: number
  created_at?: string
  updated_at?: string
}

export interface EnvironmentCreate {
  name: string
  base_url: string
  variables?: Record<string, string>
  retention_days?: number
}

export interface EnvironmentUpdate {
  name?: string
  base_url?: string
  variables?: Record<string, string>
  retention_days?: number
}

export async function getEnvironments(): Promise<Environment[]> {
  const response = await api.get('/environments')
  return response.data
}

export async function getEnvironment(id: string): Promise<Environment> {
  const response = await api.get(`/environments/${id}`)
  return response.data
}

export async function createEnvironment(data: EnvironmentCreate): Promise<Environment> {
  const response = await api.post('/environments', data)
  return response.data
}

export async function updateEnvironment(id: string, data: EnvironmentUpdate): Promise<Environment> {
  const response = await api.put(`/environments/${id}`, data)
  return response.data
}

export async function deleteEnvironment(id: string): Promise<void> {
  await api.delete(`/environments/${id}`)
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

// API Keys
export interface ApiKey {
  id: string
  name: string
  key_prefix: string
  created_at: string
  last_used_at: string | null
}

export interface CreateApiKeyResponse {
  id: string
  name: string
  key: string  // Full key, only shown once
  key_prefix: string
  created_at: string
}

export async function listApiKeys(): Promise<ApiKey[]> {
  const response = await api.get('/auth/keys')
  return response.data
}

export async function createApiKey(name: string): Promise<CreateApiKeyResponse> {
  const response = await api.post('/auth/keys', { name })
  return response.data
}

export async function revokeApiKey(id: string): Promise<void> {
  await api.delete(`/auth/keys/${id}`)
}

// Custom Steps
export interface CustomStep {
  id: string
  name: string
  pattern: string
  description?: string
  implementation: string
  created_at?: string
  updated_at?: string
}

export interface CustomStepCreate {
  name: string
  pattern: string
  description?: string
  implementation: string
}

export interface CustomStepUpdate {
  name?: string
  pattern?: string
  description?: string
  implementation?: string
}

export async function listCustomSteps(): Promise<CustomStep[]> {
  const response = await api.get('/steps')
  return response.data
}

export async function getCustomStep(id: string): Promise<CustomStep> {
  const response = await api.get(`/steps/${id}`)
  return response.data
}

export async function createCustomStep(data: CustomStepCreate): Promise<CustomStep> {
  const response = await api.post('/steps', data)
  return response.data
}

export async function updateCustomStep(id: string, data: CustomStepUpdate): Promise<CustomStep> {
  const response = await api.put(`/steps/${id}`, data)
  return response.data
}

export async function deleteCustomStep(id: string): Promise<void> {
  await api.delete(`/steps/${id}`)
}

// Scenario Content (for editor)
export interface ScenarioContent {
  id: string
  name: string
  feature_path: string
  repo_id?: string
  repo_name?: string
  tags: string[]
  content: string
}

export async function getScenarioContent(id: string): Promise<ScenarioContent> {
  const response = await api.get(`/scenarios/${id}/content`)
  return response.data
}

export async function updateScenarioContent(id: string, content: string): Promise<ScenarioContent> {
  const response = await api.put(`/scenarios/${id}/content`, { content })
  return response.data
}
