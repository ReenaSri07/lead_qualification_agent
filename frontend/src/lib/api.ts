/**
 * API client for communicating with the Lead Qualification backend.
 * All API calls go through the Vite proxy to localhost:8000.
 */

export interface SubmitLeadInput {
  name?: string;
  email?: string;
  company?: string;
  role?: string;
  source?: string;
  notes?: string;
}

const BASE_URL = '/api/v1';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Leads
  submitLead: (data: SubmitLeadInput) =>
    request<{ lead_id: number; status: string; classification: string; score: number; errors: string[] }>('/leads', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getLeads: (params?: { status?: string; classification?: string; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.classification) searchParams.set('classification', params.classification);
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    const query = searchParams.toString();
    return request<{ total: number; leads: any[]; limit: number; offset: number }>(`/leads${query ? `?${query}` : ''}`);
  },

  getLead: (id: number) =>
    request<any>(`/leads/${id}`),

  // Approval
  approveLead: (id: number) =>
    request<{ message: string; lead_id: number }>(`/leads/${id}/approve`, { method: 'POST' }),

  rejectLead: (id: number, reason?: string) =>
    request<{ message: string; lead_id: number }>(`/leads/${id}/reject${reason ? `?reason=${encodeURIComponent(reason)}` : ''}`, { method: 'POST' }),

  editAndApproveEmail: (id: number, subject: string, body: string) =>
    request<{ message: string; lead_id: number }>(`/leads/${id}/edit-email?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`, { method: 'POST' }),

  sendEmail: (id: number) =>
    request<{ message: string; lead_id: number }>(`/leads/${id}/send`, { method: 'POST' }),

  // Analytics
  getAnalytics: () =>
    request<{ total_leads: number; hot: number; nurture: number; disqualified: number; average_score: number; emails_approved: number; emails_sent: number; pending_approval: number }>('/analytics'),

  // Audit Logs
  getAuditLogs: (leadId?: number) =>
    request<{ logs: any[]; total: number }>(`/audit-logs${leadId ? `?lead_id=${leadId}` : ''}`),
};