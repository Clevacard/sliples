import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Scenarios from './pages/Scenarios'
import ScenarioEditor from './pages/ScenarioEditor'
import TestRuns from './pages/TestRuns'
import RunDetails from './pages/RunDetails'
import Environments from './pages/Environments'
import Repos from './pages/Repos'
import Settings from './pages/Settings'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="scenarios" element={<Scenarios />} />
        <Route path="scenarios/:id" element={<ScenarioEditor />} />
        <Route path="runs" element={<TestRuns />} />
        <Route path="runs/:id" element={<RunDetails />} />
        <Route path="environments" element={<Environments />} />
        <Route path="repos" element={<Repos />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
