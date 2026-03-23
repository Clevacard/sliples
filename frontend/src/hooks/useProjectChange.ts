import { useEffect, useRef } from 'react'
import { useProjectsStore } from '../store/projects'
import { useEnvironmentsStore } from '../store/environments'
import { useSchedulesStore } from '../store/schedules'
import { useTestRunsStore } from '../store/testRuns'
import { useCustomStepsStore } from '../store/customSteps'
import { useDashboardStore } from '../store/dashboard'
import { usePagesStore } from '../store/pages'

/**
 * Hook that refreshes all project-scoped data when the current project changes.
 * Should be used once in the app layout component.
 */
export function useProjectChange() {
  const currentProject = useProjectsStore((state) => state.currentProject)
  const previousProjectId = useRef<string | null>(null)

  const fetchEnvironments = useEnvironmentsStore((state) => state.fetchEnvironments)
  const fetchSchedules = useSchedulesStore((state) => state.fetchSchedules)
  const fetchRuns = useTestRunsStore((state) => state.fetchRuns)
  const fetchSteps = useCustomStepsStore((state) => state.fetchSteps)
  const fetchDashboardData = useDashboardStore((state) => state.fetchDashboardData)
  const fetchPages = usePagesStore((state) => state.fetchPages)

  useEffect(() => {
    const currentId = currentProject?.id ?? null

    // Skip if project hasn't changed
    if (currentId === previousProjectId.current) {
      return
    }

    // Update previous project ID
    previousProjectId.current = currentId

    // Only refresh if we have a project (or if switching from a project to none)
    if (currentId !== null || previousProjectId.current !== null) {
      // Refresh all project-scoped stores
      fetchEnvironments()
      fetchSchedules()
      fetchRuns()
      fetchSteps()
      fetchDashboardData()
      fetchPages()
    }
  }, [currentProject, fetchEnvironments, fetchSchedules, fetchRuns, fetchSteps, fetchDashboardData, fetchPages])

  return currentProject
}

/**
 * Hook to get the current project ID for use in components.
 */
export function useCurrentProjectId(): string | null {
  return useProjectsStore((state) => state.currentProject?.id ?? null)
}
