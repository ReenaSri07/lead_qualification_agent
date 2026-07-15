import React, { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { FileText, Search, RefreshCw } from 'lucide-react'

interface AuditEntry {
  id: number
  lead_id: number | null
  action: string
  tool_name: string | null
  classification: string | null
  score: number | null
  reason: string | null
  approval_status: string | null
  timestamp: string
}

export default function AuditLogs() {
  const [logs, setLogs] = useState<AuditEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    loadLogs()
  }, [])

  async function loadLogs() {
    setLoading(true)
    try {
      const data = await api.getAuditLogs()
      setLogs(data.logs)
    } catch (e) {
      console.error('Failed to load audit logs:', e)
    } finally {
      setLoading(false)
    }
  }

  function getActionColor(action: string) {
    if (action.includes('INJECTION')) return 'text-red-600 bg-red-50'
    if (action.includes('APPROVED')) return 'text-green-600 bg-green-50'
    if (action.includes('REJECTED')) return 'text-red-600 bg-red-50'
    if (action.includes('HOT')) return 'text-red-600 bg-red-50'
    if (action.includes('NURTURE')) return 'text-amber-600 bg-amber-50'
    if (action.includes('DISQUALIFY')) return 'text-green-600 bg-green-50'
    if (action.includes('ERROR')) return 'text-red-600 bg-red-50'
    return 'text-blue-600 bg-blue-50'
  }

  const filteredLogs = logs.filter((log) => {
    if (!searchTerm) return true
    const term = searchTerm.toLowerCase()
    return (
      log.action.toLowerCase().includes(term) ||
      (log.tool_name && log.tool_name.toLowerCase().includes(term)) ||
      (log.classification && log.classification.toLowerCase().includes(term)) ||
      (log.reason && log.reason.toLowerCase().includes(term))
    )
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
          <p className="text-sm text-gray-500 mt-1">
            Complete audit trail of all tool calls, decisions, and actions
          </p>
        </div>
        <button
          onClick={loadLogs}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search audit logs..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="flex gap-1">
            <div className="loading-dot w-2 h-2 bg-blue-500 rounded-full" />
            <div className="loading-dot w-2 h-2 bg-blue-500 rounded-full" />
            <div className="loading-dot w-2 h-2 bg-blue-500 rounded-full" />
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="divide-y divide-gray-100">
            {filteredLogs.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-500">
                No audit logs found.
              </div>
            ) : (
              filteredLogs.map((log) => (
                <div key={log.id} className="p-4 hover:bg-gray-50">
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${getActionColor(log.action)}`}>
                      <FileText className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getActionColor(log.action)}`}>
                          {log.action}
                        </span>
                        {log.tool_name && (
                          <span className="text-xs text-gray-500">{log.tool_name}</span>
                        )}
                        {log.classification && (
                          <span className="text-xs font-medium">{log.classification}</span>
                        )}
                        {log.score != null && (
                          <span className="text-xs text-gray-500">Score: {log.score}</span>
                        )}
                      </div>
                      {log.reason && (
                        <p className="text-sm text-gray-600 truncate">{log.reason}</p>
                      )}
                      {log.approval_status && (
                        <p className="text-xs text-gray-500 mt-1">
                          Approval: {log.approval_status}
                        </p>
                      )}
                      <p className="text-xs text-gray-400 mt-1">
                        {log.timestamp ? new Date(log.timestamp).toLocaleString() : ''}
                        {log.lead_id && ` · Lead #${log.lead_id}`}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}