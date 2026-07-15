export interface Lead {
  id: number;
  name: string | null;
  email: string | null;
  company: string | null;
  role: string | null;
  source: string | null;
  notes: string | null;
  enriched_profile: Record<string, unknown> | null;
  total_score: number | null;
  dimension_scores: Record<string, number> | null;
  scoring_reasoning: string | null;
  scoring_evidence: string | null;
  classification: string | null;
  classification_reason: string | null;
  classification_confidence: number | null;
  email_subject: string | null;
  email_body: string | null;
  email_draft_version: number | null;
  approval_status: string;
  routing_action: string | null;
  routing_reason: string | null;
  status: string;
  crm_status: string | null;
  error_message: string | null;
  created_at: string | null;
  updated_at: string | null;
  processed_at: string | null;
  email_sent_at: string | null;
}

export interface Analytics {
  total_leads: number;
  hot: number;
  nurture: number;
  disqualified: number;
  average_score: number;
  emails_approved: number;
  emails_sent: number;
  pending_approval: number;
}

export interface AuditLogEntry {
  id: number;
  lead_id: number | null;
  action: string;
  tool_name: string | null;
  classification: string | null;
  score: number | null;
  reason: string | null;
  approval_status: string | null;
  timestamp: string;
}

export interface EvaluationResult {
  test_name: string;
  passed: boolean;
  errors: string | null;
}