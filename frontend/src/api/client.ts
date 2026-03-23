import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

/**
 * Get the WebSocket URL for a given path.
 * Automatically converts http:// to ws:// and https:// to wss://
 */
export function getWebSocketUrl(path: string): string {
  let baseUrl = API_URL || window.location.origin
  // Convert http(s) to ws(s)
  baseUrl = baseUrl.replace(/^http/, 'ws')
  // Ensure path starts with /
  if (!path.startsWith('/')) {
    path = '/' + path
  }
  return `${baseUrl}${path}`
}

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies for session auth
})

// Add project context to requests
// Note: We rely on httpOnly cookies for JWT auth in the browser.
// API keys are only for CI/CD use (curl, scripts), not the web UI.
api.interceptors.request.use((config) => {
  // Add current project ID to all requests
  const currentProjectId = localStorage.getItem('sliples_current_project_id')
  if (currentProjectId) {
    config.headers['X-Project-Id'] = currentProjectId
  }

  return config
})

// Health check
export async function checkHealth() {
  const response = await api.get('/health')
  return response.data
}

// Projects
export type ProjectRole = 'owner' | 'admin' | 'member' | 'viewer'

export interface Project {
  id: string
  name: string
  slug: string
  description?: string
  created_at: string
  updated_at: string
  member_count?: number
  current_user_role?: ProjectRole
}

export interface ProjectMember {
  id: string
  user_id: string
  email: string
  name: string
  role: ProjectRole
  created_at: string
}

export interface ProjectCreate {
  name: string
  slug?: string
  description?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
}

export async function getProjects(): Promise<Project[]> {
  const response = await api.get('/projects')
  return response.data
}

export async function getProject(id: string): Promise<Project & { members: ProjectMember[] }> {
  const response = await api.get(`/projects/${id}`)
  return response.data
}

export async function createProject(data: ProjectCreate): Promise<Project> {
  const response = await api.post('/projects', data)
  return response.data
}

export async function updateProject(id: string, data: ProjectUpdate): Promise<Project> {
  const response = await api.put(`/projects/${id}`, data)
  return response.data
}

export async function deleteProject(id: string): Promise<void> {
  await api.delete(`/projects/${id}`)
}

export async function getProjectMembers(projectId: string): Promise<ProjectMember[]> {
  const response = await api.get(`/projects/${projectId}/members`)
  return response.data
}

export async function addProjectMember(projectId: string, email: string, role: ProjectRole): Promise<ProjectMember> {
  const response = await api.post(`/projects/${projectId}/members`, { email, role })
  return response.data
}

export async function updateProjectMemberRole(projectId: string, userId: string, role: ProjectRole): Promise<ProjectMember> {
  const response = await api.put(`/projects/${projectId}/members/${userId}`, { role })
  return response.data
}

export async function removeProjectMember(projectId: string, userId: string): Promise<void> {
  await api.delete(`/projects/${projectId}/members/${userId}`)
}

export async function transferProjectOwnership(projectId: string, newOwnerUserId: string): Promise<Project> {
  const response = await api.post(`/projects/${projectId}/transfer-ownership?new_owner_user_id=${newOwnerUserId}`)
  return response.data
}

// Environments
export interface Environment {
  id: string
  project_id?: string
  name: string
  base_url: string
  locale?: string
  timezone_id?: string
  credentials_env?: string
  variables: Record<string, string>
  retention_days: number
  created_at?: string
  updated_at?: string
}

export interface EnvironmentCreate {
  name: string
  base_url: string
  locale?: string
  timezone_id?: string
  variables?: Record<string, string>
  retention_days?: number
}

export interface EnvironmentUpdate {
  name?: string
  base_url?: string
  locale?: string
  timezone_id?: string
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

export async function createScenario(data: {
  name: string
  feature_path: string
  content: string
  tags?: string[]
  repo_id?: string
}) {
  const response = await api.post('/scenarios', data)
  return response.data
}

export async function deleteScenario(id: string) {
  await api.delete(`/scenarios/${id}`)
}

export async function syncScenarios() {
  const response = await api.post('/scenarios/sync')
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

export async function retryTestRun(id: string) {
  const response = await api.post(`/runs/${id}/retry`)
  return response.data
}

export async function regenerateReport(id: string) {
  const response = await api.post(`/runs/${id}/report`)
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
  project_id?: string
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

// System Configuration
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

export async function getSystemConfig(): Promise<SystemConfig> {
  const response = await api.get('/settings/system')
  return response.data
}

// Custom Steps
export interface CustomStep {
  id: string
  project_id?: string
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

// User Management
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

export async function listUsers(search?: string): Promise<UserInfo[]> {
  const response = await api.get('/users', { params: search ? { search } : undefined })
  return response.data
}

export async function getUser(id: string): Promise<UserInfo> {
  const response = await api.get(`/users/${id}`)
  return response.data
}

export async function updateUserRole(id: string, role: 'admin' | 'user'): Promise<UserInfo> {
  const response = await api.put(`/users/${id}/role`, { role })
  return response.data
}

export async function toggleUserActive(id: string, isActive: boolean): Promise<UserInfo> {
  const response = await api.put(`/users/${id}/active`, { is_active: isActive })
  return response.data
}

// Schedules
export interface Schedule {
  id: string
  project_id?: string
  name: string
  cron_expression: string
  cron_description: string
  scenario_tags: string[]
  scenario_ids: string[]
  environment_ids: string[]
  environment_names: string[]
  // Backwards compatibility
  environment_id?: string
  environment_name?: string | null
  browsers: string[]
  enabled: boolean
  created_by: string | null
  last_run_at: string | null
  next_run_at: string | null
  last_run_id: string | null
  created_at: string
  updated_at: string
}

export interface ScheduleCreate {
  name: string
  cron_expression: string
  scenario_tags?: string[]
  scenario_ids?: string[]
  environment_ids: string[]
  browsers?: string[]
  enabled?: boolean
}

export interface ScheduleUpdate {
  name?: string
  cron_expression?: string
  scenario_tags?: string[]
  scenario_ids?: string[]
  environment_ids?: string[]
  browsers?: string[]
  enabled?: boolean
}

export interface CronDescription {
  expression: string
  description: string
  next_runs: string[]
}

export async function listSchedules(enabledOnly?: boolean): Promise<Schedule[]> {
  const response = await api.get('/schedules', { params: enabledOnly ? { enabled_only: true } : undefined })
  return response.data
}

export async function getSchedule(id: string): Promise<Schedule> {
  const response = await api.get(`/schedules/${id}`)
  return response.data
}

export async function createSchedule(data: ScheduleCreate): Promise<Schedule> {
  const response = await api.post('/schedules', data)
  return response.data
}

export async function updateSchedule(id: string, data: ScheduleUpdate): Promise<Schedule> {
  const response = await api.put(`/schedules/${id}`, data)
  return response.data
}

export async function deleteSchedule(id: string): Promise<void> {
  await api.delete(`/schedules/${id}`)
}

export async function toggleSchedule(id: string): Promise<Schedule> {
  const response = await api.post(`/schedules/${id}/toggle`)
  return response.data
}

export async function runScheduleNow(id: string): Promise<{ message: string; schedule_id: string; task_id: string }> {
  const response = await api.post(`/schedules/${id}/run-now`)
  return response.data
}

export async function describeCron(expression: string): Promise<CronDescription> {
  const response = await api.get('/schedules/cron/describe', { params: { expression } })
  return response.data
}

// =============================================================================
// Test Sessions (Interactive Testing Mode)
// =============================================================================

export interface TestSession {
  id: string
  status: 'active' | 'paused' | 'completed' | 'terminated'
  browser_type: string
  environment_name: string
  environment_base_url: string
  scenario_name: string | null
  current_step_index: number
  total_steps: number
  started_at: string
  last_activity: string
  websocket_url: string
}

export interface TestSessionCreate {
  scenario_id?: string
  environment_id: string
  browser_type?: string
}

export interface StepExecuteResponse {
  step_name: string
  status: 'passed' | 'failed' | 'skipped' | 'error' | 'completed'
  duration_ms: number
  error_message: string | null
  screenshot_base64: string | null
  current_url: string | null
  page_title: string | null
  next_step_index: number
  total_steps: number
}

export interface SessionStatusResponse {
  id: string
  status: string
  current_step_index: number
  total_steps: number
  current_url: string | null
  page_title: string | null
  step_results: Array<{
    step_index: number
    step_name: string
    status: string
    duration_ms: number
    error_message: string | null
    executed_at: string
  }>
  logs: string[]
}

export interface LoadScenarioResponse {
  steps: Array<{
    index: number
    keyword: string
    text: string
    full: string
    status: string
  }>
  total_steps: number
}

export interface ScreenshotResponse {
  screenshot_base64: string
  current_url: string | null
  page_title: string | null
}

/**
 * Start a new interactive test session
 */
export async function startTestSession(data: TestSessionCreate): Promise<TestSession> {
  const response = await api.post('/test-session/start', data)
  return response.data
}

/**
 * List all test sessions
 */
export async function listTestSessions(activeOnly: boolean = true): Promise<TestSession[]> {
  const response = await api.get('/test-sessions', { params: { active_only: activeOnly } })
  return response.data
}

/**
 * Load a scenario into an active session
 */
export async function loadScenarioIntoSession(
  sessionId: string,
  data: { scenario_id?: string; content?: string }
): Promise<LoadScenarioResponse> {
  const response = await api.post(`/test-session/${sessionId}/load-scenario`, data)
  return response.data
}

/**
 * Execute the next step in a test session
 */
export async function executeStep(
  sessionId: string,
  stepIndex?: number
): Promise<StepExecuteResponse> {
  const response = await api.post(`/test-session/${sessionId}/step`, { step_index: stepIndex })
  return response.data
}

/**
 * Skip the current step
 */
export async function skipStep(sessionId: string): Promise<StepExecuteResponse> {
  const response = await api.post(`/test-session/${sessionId}/skip`)
  return response.data
}

/**
 * Take a screenshot
 */
export async function takeScreenshot(sessionId: string): Promise<ScreenshotResponse> {
  const response = await api.post(`/test-session/${sessionId}/screenshot`)
  return response.data
}

/**
 * Get session status
 */
export async function getSessionStatus(sessionId: string): Promise<SessionStatusResponse> {
  const response = await api.get(`/test-session/${sessionId}/status`)
  return response.data
}

/**
 * Navigate to a URL
 */
export async function navigateSession(
  sessionId: string,
  url: string
): Promise<StepExecuteResponse> {
  const response = await api.post(`/test-session/${sessionId}/navigate`, { url })
  return response.data
}

/**
 * Run a custom browser action
 */
export async function runCustomAction(
  sessionId: string,
  action: string,
  selector?: string,
  value?: string
): Promise<StepExecuteResponse> {
  const response = await api.post(`/test-session/${sessionId}/action`, {
    action,
    selector: selector || '',
    value: value || '',
  })
  return response.data
}

/**
 * Pause a test session
 */
export async function pauseSession(sessionId: string): Promise<{ status: string; session_id: string }> {
  const response = await api.post(`/test-session/${sessionId}/pause`)
  return response.data
}

/**
 * Resume a paused test session
 */
export async function resumeSession(sessionId: string): Promise<{ status: string; session_id: string }> {
  const response = await api.post(`/test-session/${sessionId}/resume`)
  return response.data
}

/**
 * End a test session
 */
export async function endTestSession(sessionId: string): Promise<void> {
  await api.delete(`/test-session/${sessionId}`)
}

// =============================================================================
// Pages (Named URL Mappings)
// =============================================================================

export interface PageOverride {
  id: string
  environment_id: string
  environment_name: string | null
  path: string
  created_at: string
}

export interface Page {
  id: string
  project_id: string
  name: string
  path: string
  description: string | null
  created_at: string
  updated_at: string
  overrides: PageOverride[]
}

export interface PageCreate {
  name: string
  path: string
  description?: string
}

export interface PageUpdate {
  name?: string
  path?: string
  description?: string
}

export interface PageWithUrls {
  id: string
  project_id: string
  name: string
  path: string
  description: string | null
  urls: Record<string, string>  // environment_name -> full_url
}

export interface PageOverrideCreate {
  environment_id: string
  path: string
}

export async function listPages(): Promise<Page[]> {
  const response = await api.get('/pages')
  return response.data
}

export async function getPage(id: string): Promise<Page> {
  const response = await api.get(`/pages/${id}`)
  return response.data
}

export async function createPage(data: PageCreate): Promise<Page> {
  const response = await api.post('/pages', data)
  return response.data
}

export async function updatePage(id: string, data: PageUpdate): Promise<Page> {
  const response = await api.put(`/pages/${id}`, data)
  return response.data
}

export async function deletePage(id: string): Promise<void> {
  await api.delete(`/pages/${id}`)
}

export async function getPageUrls(id: string): Promise<PageWithUrls> {
  const response = await api.get(`/pages/${id}/urls`)
  return response.data
}

export async function createPageOverride(pageId: string, data: PageOverrideCreate): Promise<PageOverride> {
  const response = await api.post(`/pages/${pageId}/overrides`, data)
  return response.data
}

export async function deletePageOverride(pageId: string, overrideId: string): Promise<void> {
  await api.delete(`/pages/${pageId}/overrides/${overrideId}`)
}

export async function resolvePageUrl(pageName: string, environmentId: string): Promise<{
  page_name: string
  environment_name: string
  path: string
  base_url: string
  full_url: string
}> {
  const response = await api.get(`/pages/resolve/${encodeURIComponent(pageName)}`, {
    params: { environment_id: environmentId }
  })
  return response.data
}

// =============================================================================
// Gherkin Parser / Step Validation
// =============================================================================

export interface StepValidation {
  line_number: number
  keyword: string
  text: string
  full_line: string
  is_matched: boolean
  matched_pattern: string | null
  match_source: 'builtin' | 'custom' | null
  custom_step_id: string | null
}

export interface ParseResponse {
  valid: boolean
  total_steps: number
  matched_steps: number
  unmatched_steps: number
  steps: StepValidation[]
  errors: string[]
}

export async function validateGherkinSteps(content: string): Promise<ParseResponse> {
  const response = await api.post('/parser/validate', { content })
  return response.data
}

export interface BuiltinPattern {
  pattern: string
  description: string
}

export async function getBuiltinPatterns(): Promise<BuiltinPattern[]> {
  const response = await api.get('/parser/patterns')
  return response.data
}
