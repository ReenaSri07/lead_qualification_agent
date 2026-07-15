import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Flame, Sprout, XCircle, Search, RefreshCw } from 'lucide-react'
import { api } from '../lib/api'

interface LeadSummary {
  id: number
  name: string | null
  email: string | null
  company: string | null
  role: string | null
  classification: string | null
  total_score: number | null
  status: string
  approval_status: string
  routing_action: string | null
  created_at: string | null
}

export default function LeadQueue() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [leads, setLeads] = useState<LeadSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState(searchParams.get('status') || 'all')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    loadLeads()
  }, [filter])

  async function loadLeads() {
    setLoading(true)
    try {
      const params: any = { limit: 100 }
      if (filter !== 'all') {
        if (['HOT', 'NURTURE', 'DISQUALIFY'].includes(filter)) {
          params.classification = filter
        } else {
          params.status = filter
        }
      }
      const data = await api.getLeads(params)
      setLeads(data.leads)
    } catch (e) {
      console.error('Failed to load leads:', e)
    } finally {
      setLoading(false)
    }
  }

  const filteredLeads = leads.filter((lead) => {
    if (!searchTerm) return true
    const term = searchTerm.toLowerCase()
    return (
      (lead.name && lead.name.toLowerCase().includes(term)) ||
      (lead.company && lead.company.toLowerCase().includes(term)) ||
      (lead.email && lead.email.toLowerCase().includes(term))
    )
  })

  const filters = [
    { value: 'all', label: 'All' },
    { value: 'HOT', label: 'Hot', icon: Flame },
    { value: 'NURTURE', label: 'Nurture', icon: Sprout },
    { value: 'DISQUALIFY', label: 'Disqualified', icon: XCircle },
    { value: 'AWAITING_APPROVAL', label: 'Pending Approval' },
    { value: 'APPROVED', label: 'Approved' },
    { value: 'SENT', label: 'Sent' },
  ]

  function getClassificationBadge(classification: string | null) {
    switch (classification) {
      case 'HOT':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
            <Flame className="w-3 h-3" />
            HOT
          </span>
        )
      case 'NURTURE':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
            <Sprout className="w-3 h-3" />
            NURTURE
          </span>
        )
      case 'DISQUALIFY':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
            <XCircle className="w-3 h-3" />
            DISQUALIFIED
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
            PENDING
          </span>
        )
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lead Queue</h1>
          <p className="text-sm text-gray-500 mt-1">
            Browse and manage all leads in the pipeline
          </p>
        </div>
        <button
          onClick={loadLeads}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        {filters.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filter === f.value
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {f.icon && <f.icon className="w-3.5 h-3.5" />}
            {f.label}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search by name, company, or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Lead Table */}
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
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Company</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Score</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Classification</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Date</th>
              </tr>
            </thead>
            <tbody>
              {filteredLeads.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">
                    No leads found. Submit a new lead from the dashboard.
                  </td>
                </tr>
              ) : (
                filteredLeads.map((lead) => (
                  <tr
                    key={lead.id}
                    onClick={() => navigate(`/leads/${lead.id}`)}
                    className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-gray-900">{lead.name || 'Unknown'}</div>
                      <div className="text-xs text-gray-500">{lead.email}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">{lead.company || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{lead.role || '-'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              (lead.total_score || 0) >= 80
                                ? 'bg-red-500'
                                : (lead.total_score || 0) >= 50
                                ? 'bg-amber-500'
                                : 'bg-gray-400'
                            }`}
                            style={{ width: `${lead.total_score || 0}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-gray-600">
                          {lead.total_score?.toFixed(0) || '0'}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">{getClassificationBadge(lead.classification)}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-gray-600">{lead.status}</span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {lead.created_at ? new Date(lead.created_at).toLocaleDateString() : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}