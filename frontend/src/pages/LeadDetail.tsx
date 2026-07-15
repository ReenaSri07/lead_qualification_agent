import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Flame,
  Sprout,
  XCircle,
  Check,
  X,
  Send,
  Edit3,
  Loader,
  FileText,
  Shield,
  Target,
  Briefcase,
  TrendingUp,
} from 'lucide-react'
import { api } from '../lib/api'

interface LeadData {
  id: number
  name: string | null
  email: string | null
  company: string | null
  role: string | null
  source: string | null
  notes: string | null
  enriched_profile: Record<string, any> | null
  total_score: number | null
  dimension_scores: Record<string, number> | null
  scoring_reasoning: string | null
  scoring_evidence: string | null
  classification: string | null
  classification_reason: string | null
  classification_confidence: number | null
  email_subject: string | null
  email_body: string | null
  email_draft_version: number | null
  approval_status: string
  routing_action: string | null
  routing_reason: string | null
  status: string
  error_message: string | null
  created_at: string | null
  updated_at: string | null
  processed_at: string | null
  email_sent_at: string | null
}

export default function LeadDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [lead, setLead] = useState<LeadData | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [editMode, setEditMode] = useState(false)
  const [editSubject, setEditSubject] = useState('')
  const [editBody, setEditBody] = useState('')
  const [rejectReason, setRejectReason] = useState('')
  const [showReject, setShowReject] = useState(false)

  useEffect(() => {
    if (id) loadLead(parseInt(id))
  }, [id])

  async function loadLead(leadId: number) {
    setLoading(true)
    try {
      const data = await api.getLead(leadId)
      setLead(data)
      setEditSubject(data.email_subject || '')
      setEditBody(data.email_body || '')
    } catch (e) {
      console.error('Failed to load lead:', e)
    } finally {
      setLoading(false)
    }
  }

  async function handleApprove() {
    if (!lead) return
    setActionLoading('approve')
    try {
      await api.approveLead(lead.id)
      await loadLead(lead.id)
    } catch (e) {
      console.error('Failed to approve:', e)
    } finally {
      setActionLoading(null)
    }
  }

  async function handleReject() {
    if (!lead) return
    setActionLoading('reject')
    try {
      await api.rejectLead(lead.id, rejectReason)
      await loadLead(lead.id)
      setShowReject(false)
      setRejectReason('')
    } catch (e) {
      console.error('Failed to reject:', e)
    } finally {
      setActionLoading(null)
    }
  }

  async function handleEditAndApprove() {
    if (!lead) return
    setActionLoading('edit')
    try {
      await api.editAndApproveEmail(lead.id, editSubject, editBody)
      await loadLead(lead.id)
      setEditMode(false)
    } catch (e) {
      console.error('Failed to edit and approve:', e)
    } finally {
      setActionLoading(null)
    }
  }

  async function handleSend() {
    if (!lead) return
    setActionLoading('send')
    try {
      await api.sendEmail(lead.id)
      await loadLead(lead.id)
    } catch (e) {
      console.error('Failed to send:', e)
    } finally {
      setActionLoading(null)
    }
  }

  function getClassificationDisplay() {
    switch (lead?.classification) {
      case 'HOT':
        return { icon: Flame, color: 'text-red-600', bg: 'bg-red-50', text: 'HOT' }
      case 'NURTURE':
        return { icon: Sprout, color: 'text-amber-600', bg: 'bg-amber-50', text: 'NURTURE' }
      case 'DISQUALIFY':
        return { icon: XCircle, color: 'text-green-600', bg: 'bg-green-50', text: 'DISQUALIFIED' }
      default:
        return { icon: Loader, color: 'text-gray-600', bg: 'bg-gray-50', text: 'PENDING' }
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex gap-1">
          <div className="loading-dot w-2 h-2 bg-blue-500 rounded-full" />
          <div className="loading-dot w-2 h-2 bg-blue-500 rounded-full" />
          <div className="loading-dot w-2 h-2 bg-blue-500 rounded-full" />
        </div>
      </div>
    )
  }

  if (!lead) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Lead not found</p>
        <button onClick={() => navigate('/leads')} className="mt-4 text-blue-600 hover:underline">
          Back to Lead Queue
        </button>
      </div>
    )
  }

  const cls = getClassificationDisplay()
  const ClassIcon = cls.icon

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/leads')} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{lead.name || 'Unknown Lead'}</h1>
            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${cls.bg} ${cls.color}`}>
              <ClassIcon className="w-4 h-4" />
              {cls.text}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {lead.company ? `${lead.company} · ` : ''}{lead.role || ''}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Lead Information */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-gray-500" />
              Lead Information
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500">Name</label>
                <p className="text-sm font-medium">{lead.name || 'Unknown'}</p>
              </div>
              <div>
                <label className="text-xs text-gray-500">Email</label>
                <p className="text-sm font-medium">{lead.email || 'Unknown'}</p>
              </div>
              <div>
                <label className="text-xs text-gray-500">Company</label>
                <p className="text-sm font-medium">{lead.company || 'Unknown'}</p>
              </div>
              <div>
                <label className="text-xs text-gray-500">Role</label>
                <p className="text-sm font-medium">{lead.role || 'Unknown'}</p>
              </div>
              <div>
                <label className="text-xs text-gray-500">Source</label>
                <p className="text-sm font-medium">{lead.source || 'Unknown'}</p>
              </div>
              <div>
                <label className="text-xs text-gray-500">Status</label>
                <p className="text-sm font-medium">{lead.status}</p>
              </div>
            </div>
            {lead.notes && (
              <div className="mt-4">
                <label className="text-xs text-gray-500">Notes</label>
                <p className="text-sm mt-1 text-gray-700">{lead.notes}</p>
              </div>
            )}
          </div>

          {/* Enriched Profile */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Target className="w-4 h-4 text-gray-500" />
              Enriched Profile
            </h2>
            {lead.enriched_profile ? (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-500">Industry</label>
                  <p className="text-sm font-medium">{lead.enriched_profile.industry || 'Unknown'}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500">Company Size</label>
                  <p className="text-sm font-medium">{lead.enriched_profile.company_size || 'Unknown'}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500">Location</label>
                  <p className="text-sm font-medium">{lead.enriched_profile.location || 'Unknown'}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500">Decision Maker Level</label>
                  <p className="text-sm font-medium">{lead.enriched_profile.decision_maker_level || 'Unknown'}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500">Funding</label>
                  <p className="text-sm font-medium">{lead.enriched_profile.funding || 'Unknown'}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500">Recent News</label>
                  <p className="text-sm font-medium">{lead.enriched_profile.recent_news || 'Unknown'}</p>
                </div>
                {lead.enriched_profile.buying_signals?.length > 0 && (
                  <div className="col-span-2">
                    <label className="text-xs text-gray-500">Buying Signals</label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {lead.enriched_profile.buying_signals.map((signal: string, i: number) => (
                        <span key={i} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full">{signal}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No enrichment data available</p>
            )}
          </div>

          {/* Scoring Reasoning */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FileText className="w-4 h-4 text-gray-500" />
              Scoring Reasoning
            </h2>
            <p className="text-sm text-gray-700">{lead.scoring_reasoning || 'No reasoning available'}</p>
            {lead.scoring_evidence && (
              <div className="mt-4">
                <label className="text-xs text-gray-500">Evidence</label>
                <p className="text-sm mt-1 text-gray-700">{lead.scoring_evidence}</p>
              </div>
            )}
          </div>

          {/* Classification Reason */}
          {lead.classification_reason && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Shield className="w-4 h-4 text-gray-500" />
                Classification Decision
              </h2>
              <p className="text-sm text-gray-700">{lead.classification_reason}</p>
              {lead.classification_confidence && (
                <div className="mt-3">
                  <label className="text-xs text-gray-500">Confidence</label>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full" style={{ width: `${lead.classification_confidence}%` }} />
                    </div>
                    <span className="text-sm font-medium">{lead.classification_confidence.toFixed(0)}%</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Email Draft */}
          {(lead.email_subject || lead.email_body) && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Send className="w-4 h-4 text-gray-500" />
                Email Draft {lead.email_draft_version ? `(v${lead.email_draft_version})` : ''}
              </h2>
              {editMode ? (
                <div className="space-y-3">
                  <input type="text" value={editSubject} onChange={(e) => setEditSubject(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg text-sm font-medium" placeholder="Subject" />
                  <textarea value={editBody} onChange={(e) => setEditBody(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg text-sm" rows={8} placeholder="Email body" />
                  <div className="flex justify-end gap-2">
                    <button onClick={() => setEditMode(false)} className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
                    <button onClick={handleEditAndApprove} disabled={actionLoading === 'edit'}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                      {actionLoading === 'edit' ? 'Saving...' : 'Save & Approve'}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="p-3 bg-gray-50 rounded-lg mb-3">
                    <p className="text-sm font-medium text-gray-900">Subject: {lead.email_subject}</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg whitespace-pre-wrap text-sm text-gray-700">
                    {lead.email_body}
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Score Card */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-gray-500" />
              Score Card
            </h2>
            <div className="text-center mb-4">
              <div className="text-4xl font-bold text-gray-900">{lead.total_score?.toFixed(0) || '0'}</div>
              <div className="text-sm text-gray-500">/ 100</div>
            </div>
            {lead.dimension_scores && (
              <div className="space-y-3">
                {Object.entries(lead.dimension_scores).map(([key, value]) => (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="font-medium">{value.toFixed(0)}</span>
                    </div>
                    <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${value >= 80 ? 'bg-green-500' : value >= 50 ? 'bg-amber-500' : 'bg-gray-400'}`}
                        style={{ width: `${value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Approval Panel */}
          {lead.classification === 'HOT' && lead.approval_status === 'AWAITING_APPROVAL' && (
            <div className="bg-white rounded-xl border-2 border-amber-200 p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-4">Approval Required</h2>
              <p className="text-xs text-gray-500 mb-4">This email requires human approval before it can be sent.</p>
              <div className="space-y-3">
                <button onClick={handleApprove} disabled={actionLoading === 'approve'}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm font-medium">
                  <Check className="w-4 h-4" />
                  {actionLoading === 'approve' ? 'Approving...' : 'Approve Email'}
                </button>
                <button onClick={() => setEditMode(true)} disabled={actionLoading === 'edit'}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium">
                  <Edit3 className="w-4 h-4" />
                  Edit & Approve
                </button>
                <button onClick={() => setShowReject(true)} disabled={actionLoading === 'reject'}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 disabled:opacity-50 text-sm font-medium">
                  <X className="w-4 h-4" />
                  Reject
                </button>
              </div>
              {showReject && (
                <div className="mt-4 space-y-2">
                  <textarea value={rejectReason} onChange={(e) => setRejectReason(e.target.value)}
                    placeholder="Reason for rejection (optional)" className="w-full px-3 py-2 border rounded-lg text-sm" rows={2} />
                  <div className="flex gap-2">
                    <button onClick={() => setShowReject(false)} className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
                    <button onClick={handleReject} disabled={actionLoading === 'reject'}
                      className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50">
                      {actionLoading === 'reject' ? 'Rejecting...' : 'Confirm Reject'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Approved State */}
          {lead.approval_status === 'APPROVED' && lead.status !== 'SENT' && (
            <div className="bg-white rounded-xl border-2 border-green-200 p-5">
              <div className="flex items-center gap-2 text-green-700 mb-3">
                <Check className="w-5 h-5" />
                <span className="font-medium">Approved</span>
              </div>
              <button onClick={handleSend} disabled={actionLoading === 'send'}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium">
                <Send className="w-4 h-4" />
                {actionLoading === 'send' ? 'Sending...' : 'Send Email Now'}
              </button>
            </div>
          )}

          {/* Rejected State */}
          {lead.approval_status === 'REJECTED' && (
            <div className="bg-white rounded-xl border-2 border-red-200 p-5">
              <div className="flex items-center gap-2 text-red-700">
                <X className="w-5 h-5" />
                <span className="font-medium">Rejected</span>
              </div>
              {lead.error_message && <p className="text-sm text-gray-500 mt-2">{lead.error_message}</p>}
            </div>
          )}

          {/* Sent State */}
          {lead.status === 'SENT' && (
            <div className="bg-white rounded-xl border-2 border-green-200 p-5">
              <div className="flex items-center gap-2 text-green-700">
                <Send className="w-5 h-5" />
                <span className="font-medium">Email Sent</span>
              </div>
              {lead.email_sent_at && (
                <p className="text-xs text-gray-500 mt-2">Sent at: {new Date(lead.email_sent_at).toLocaleString()}</p>
              )}
            </div>
          )}

          {/* Nurture/Disqualified Info */}
          {lead.classification === 'NURTURE' && (
            <div className="bg-white rounded-xl border border-amber-200 p-5">
              <div className="flex items-center gap-2 text-amber-700 mb-2">
                <Sprout className="w-5 h-5" />
                <span className="font-medium">Nurture Pipeline</span>
              </div>
              <p className="text-sm text-gray-600">{lead.routing_reason || 'Lead moved to nurture pipeline.'}</p>
            </div>
          )}
          {lead.classification === 'DISQUALIFY' && (
            <div className="bg-white rounded-xl border border-green-200 p-5">
              <div className="flex items-center gap-2 text-green-700 mb-2">
                <XCircle className="w-5 h-5" />
                <span className="font-medium">Disqualified</span>
              </div>
              <p className="text-sm text-gray-600">{lead.routing_reason || 'Lead archived.'}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}