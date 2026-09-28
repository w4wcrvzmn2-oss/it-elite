import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppLayout } from './components/layout/AppLayout'
import { Dashboard } from './pages/Dashboard'
import { ProjectOverview } from './pages/ProjectOverview'
import { MapWorkspace } from './pages/MapWorkspace'
import { PlantingPage } from './pages/PlantingPage'
import { AnalysisPage } from './pages/AnalysisPage'
import { ConstraintsPage } from './pages/ConstraintsPage'
import { ReportPage } from './pages/ReportPage'
import { ScenariosPage } from './pages/ScenariosPage'
import { SettingsPage } from './pages/SettingsPage'
import { VisualizationPage } from './pages/VisualizationPage'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/project" element={<AppLayout />}>
            <Route index element={<ProjectOverview />} />
            <Route path="map" element={<MapWorkspace />} />
            <Route path="planting" element={<PlantingPage />} />
            <Route path="analysis" element={<AnalysisPage />} />
            <Route path="constraints" element={<ConstraintsPage />} />
            <Route path="scenarios" element={<ScenariosPage />} />
            <Route path="visualization" element={<VisualizationPage />} />
            <Route path="report" element={<ReportPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
