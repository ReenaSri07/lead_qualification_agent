import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  TrendingUp,
  Users,
  Flame,
  Sprout,
  XCircle,
  Mail,
  Send,
  Clock,
  Plus,
} from 'lucide-react'
import { api } from '../lib/api'

interface Analytics {
  total_leads: number
  hot: number
  nurture: number
  disqualified: number
  average_score: number
  emails_approved: number
  emails_sent: number
  pending_approval: number
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [showNewLead, setShowNewLead] = useState(false)
  const [newLead, setNewLead] = useState({
    name: '',
    email: '',
    company: '',
    role: '',
    source: '',
    notes: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null)

  useEffect(() => {
    loadAnalytics()
  }, [])

  async function loadAnalytics() {
    try {
      const data = await api.getAnalytics()
      setAnalytics(data)
    } catch (e) {
      console.error('Failed to load analytics:', e)
    }
  }

  async function handleSubmitLead(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setSubmitError(null)
    setSubmitSuccess(null)
    try {
      const result = await api.submitLead(newLead)
      setSubmitSuccess(
        `Lead submitted! Classification: ${result.classification ?? 'Processing…'}, Score: ${result.score ?? 'N/A'}`
      )
      setNewLead({ name: '', email: '', company: '', role: '', source: '', notes: '' })
      await loadAnalytics()
      // Auto-close modal after 2 seconds on success
      setTimeout(() => {
        setShowNewLead(false)
        setSubmitSuccess(null)
      }, 2000)
    } catch (e: any) {
      const msg = e?.message ?? 'Unknown error. Please check the backend is running.'
      setSubmitError(msg)
      console.error('Failed to submit lead:', e)
    } finally {
      setSubmitting(false)
    }
  }

  const stats = [
    {
      label: 'Total Leads',
      value: analytics?.total_leads ?? 0,
      icon: Users,
      color: 'bg-blue-500',
      textColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      label: 'Hot',
      value: analytics?.hot ?? 0,
      icon: Flame,
      color: 'bg-red-500',
      textColor: 'text-red-600',
      bgColor: 'bg-red-50',
    },
    {
      label: 'Nurture',
      value: analytics?.nurture ?? 0,
      icon: Sprout,
      color: 'bg-amber-500',
      textColor: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
    {
      label: 'Disqualified',
      value: analytics?.disqualified ?? 0,
      icon: XCircle,
      color: 'bg-green-500',
      textColor: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      label: 'Avg Score',
      value: analytics?.average_score ?? 0,
      suffix: '/100',
      icon: TrendingUp,
      color: 'bg-purple-500',
      textColor: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      label: 'Emails Approved',
      value: analytics?.emails_approved ?? 0,
      icon: Mail,
      color: 'bg-indigo-500',
      textColor: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
    },
    {
      label: 'Emails Sent',
      value: analytics?.emails_sent ?? 0,
      icon: Send,
      color: 'bg-teal-500',
      textColor: 'text-teal-600',
      bgColor: 'bg-teal-50',
    },
    {
      label: 'Pending Approval',
      value: analytics?.pending_approval ?? 0,
      icon: Clock,
      color: 'bg-orange-500',
      textColor: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Lead Qualification & Outreach Agent Overview
          </p>
        </div>
        <button
          onClick={() => setShowNewLead(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          New Lead
        </button>
      </div>

      {/* New Lead Modal */}
      {showNewLead && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6">
            <h2 className="text-lg font-semibold mb-4">Submit New Lead</h2>
            {submitError && (
              <div className="mb-3 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                <strong>Error:</strong> {submitError}
              </div>
            )}
            {submitSuccess && (
              <div className="mb-3 px-3 py-2 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
                {submitSuccess}
              </div>
            )}
            <form onSubmit={handleSubmitLead} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Name"
                  value={newLead.name}
                  onChange={(e) => setNewLead({ ...newLead, name: e.target.value })}
                  className="px-3 py-2 border rounded-lg text-sm"
                />
                <input
                  type="email"
                  placeholder="Email"
                  value={newLead.email}
                  onChange={(e) => setNewLead({ ...newLead, email: e.target.value })}
                  className="px-3 py-2 border rounded-lg text-sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Company"
                  value={newLead.company}
                  onChange={(e) => setNewLead({ ...newLead, company: e.target.value })}
                  className="px-3 py-2 border rounded-lg text-sm"
                />
                <input
                  type="text"
                  placeholder="Role"
                  value={newLead.role}
                  onChange={(e) => setNewLead({ ...newLead, role: e.target.value })}
                  className="px-3 py-2 border rounded-lg text-sm"
                />
              </div>
              <input
                type="text"
                placeholder="Source (e.g., LinkedIn, Website)"
                value={newLead.source}
                onChange={(e) => setNewLead({ ...newLead, source: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              />
              <textarea
                placeholder="Notes about the lead..."
                value={newLead.notes}
                onChange={(e) => setNewLead({ ...newLead, notes: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
                rows={3}
              />
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => { setShowNewLead(false); setSubmitError(null); setSubmitSuccess(null) }}
                  className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Lead'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-500">{stat.label}</span>
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`w-4 h-4 ${stat.textColor}`} />
              </div>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-gray-900">
                {typeof stat.value === 'number' ? stat.value.toFixed(1) : stat.value}
              </span>
              {'suffix' in stat && (
                <span className="text-sm text-gray-500">{stat.suffix}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/leads')}
            className="bg-white rounded-xl border border-gray-200 p-5 text-left hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-blue-50">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <span className="font-medium text-gray-900">View Lead Queue</span>
            </div>
            <p className="text-sm text-gray-500">
              Browse and manage all leads in the pipeline
            </p>
          </button>

          <button
            onClick={() => navigate('/leads?status=PENDING_APPROVAL')}
            className="bg-white rounded-xl border border-gray-200 p-5 text-left hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-orange-50">
                <Clock className="w-5 h-5 text-orange-600" />
              </div>
              <span className="font-medium text-gray-900">Pending Approvals</span>
            </div>
            <p className="text-sm text-gray-500">
              Review and approve/reject email drafts
            </p>
          </button>

          <button
            onClick={() => navigate('/evaluation')}
            className="bg-white rounded-xl border border-gray-200 p-5 text-left hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-purple-50">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
              <span className="font-medium text-gray-900">Run Evaluation</span>
            </div>
            <p className="text-sm text-gray-500">
              Run automated tests to verify the system
            </p>
          </button>
        </div>
      </div>
    </div>
  )
}