import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
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
