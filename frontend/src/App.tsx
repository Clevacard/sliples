import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import AuthCallback from './pages/AuthCallback'
import Dashboard from './pages/Dashboard'
import Scenarios from './pages/Scenarios'
import ScenarioEditor from './pages/ScenarioEditor'
import TestRuns from './pages/TestRuns'
import RunDetails from './pages/RunDetails'
import Environments from './pages/Environments'
import Repos from './pages/Repos'
import Settings from './pages/Settings'
import CustomSteps from './pages/CustomSteps'
import Schedules from './pages/Schedules'
import Users from './pages/Users'
import TestMode from './pages/TestMode'
import Projects from './pages/Projects'
import CreateProject from './pages/CreateProject'
import ProjectSettings from './pages/ProjectSettings'
import Pages from './pages/Pages'
import AdminRoute from './components/AdminRoute'

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<AuthCallback />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/new" element={<CreateProject />} />
        <Route path="projects/:id/settings" element={<ProjectSettings />} />
        <Route path="scenarios" element={<Scenarios />} />
        <Route path="scenarios/:id" element={<ScenarioEditor />} />
        <Route path="runs" element={<TestRuns />} />
        <Route path="runs/:id" element={<RunDetails />} />
        <Route path="environments" element={<Environments />} />
        <Route path="pages" element={<Pages />} />
        <Route path="repos" element={<Repos />} />
        <Route path="custom-steps" element={<CustomSteps />} />
        <Route path="schedules" element={<Schedules />} />
        <Route path="test-mode" element={<TestMode />} />
        <Route path="settings" element={<Settings />} />
        <Route
          path="users"
          element={
            <AdminRoute>
              <Users />
            </AdminRoute>
          }
        />
      </Route>
    </Routes>
  )
}

export default App
