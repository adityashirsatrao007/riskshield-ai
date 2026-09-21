export interface Transaction {
  id: number;
  transaction_id: string;
  amount: number;
  currency: string;
  merchant_id: string;
  customer_id: string;
  timestamp: string;
  card_type: string;
  is_international: boolean;
  risk_score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  is_flagged: boolean;
  is_resolved: boolean;
  created_at: string;
  audit_trail?: AuditEntry[];
}

export interface AuditEntry {
  action: string;
  model_version: string;
  processing_time_ms: number;
  details: Record<string, unknown>;
  created_at: string;
}

export interface Alert {
  id: number;
  transaction_id: number;
  risk_score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  explanation: Explanation[];
  status: "open" | "acknowledged" | "dismissed" | "resolved";
  created_at: string;
  updated_at: string | null;
}

export interface Explanation {
  feature: string;
  value: number;
  importance: number;
  description: string;
}

export interface DashboardStats {
  total_transactions: number;
  flagged_transactions: number;
  fraud_rate: number;
  avg_risk_score: number;
  potential_savings: number;
}

export interface TimelinePoint {
  date: string;
  total: number;
  flagged: number;
  avg_score: number;
}

export interface RiskDistribution {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

export interface FalsePositiveAnalysis {
  total_flagged: number;
  resolved: number;
  estimated_false_positives: number;
  average_transaction_value: number;
  estimated_fp_cost: number;
  estimated_savings: number;
  net_benefit: number;
}

export interface AlertStats {
  total: number;
  by_status: Record<string, number>;
  by_risk_level: Record<string, number>;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  offset: number;
  limit: number;
}
