import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { RealtimeProvider } from './context/RealtimeProvider'
import ProtectedRoute from './components/auth/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Devices from './pages/Devices'
import FireEvents from './pages/FireEvents'
import Incidents from './pages/Incidents'
import IncidentDetail from './pages/IncidentDetail'
import Settings from './pages/Settings'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route element={<ProtectedRoute />}>
            <Route
              element={
                <RealtimeProvider>
                  <AppLayout />
                </RealtimeProvider>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="devices" element={<Devices />} />
              <Route path="fire-events" element={<FireEvents />} />
              <Route path="incidents" element={<Incidents />} />
              <Route path="incidents/:id" element={<IncidentDetail />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
