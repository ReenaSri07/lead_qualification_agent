import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import LeadQueue from './pages/LeadQueue'
import LeadDetail from './pages/LeadDetail'
import AuditLogs from './pages/AuditLogs'
import EvaluationDashboard from './pages/EvaluationDashboard'

function App() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/leads" element={<LeadQueue />} />
            <Route path="/leads/:id" element={<LeadDetail />} />
            <Route path="/audit-logs" element={<AuditLogs />} />
            <Route path="/evaluation" element={<EvaluationDashboard />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

export default App