import axios from "axios";
import type {
  DashboardStats,
  TimelinePoint,
  RiskDistribution,
  FalsePositiveAnalysis,
  Transaction,
  Alert,
  AlertStats,
  PaginatedResponse,
} from "./types";

const api = axios.create({
  baseURL: "/api/v1",
});

api.interceptors.request.use((config) => {
  const key = localStorage.getItem("riskshield_api_key") || "riskshield-test-key-2026";
  if (config.headers) {
    config.headers["X-API-Key"] = key;
  }
  return config;
});

export const fetchDashboard = async (): Promise<DashboardStats> => {
  const { data } = await api.get<{ success: boolean; data: DashboardStats }>(
    "/analytics/dashboard"
  );
  return data.data;
};

export const fetchTimeline = async (
  days = 30
): Promise<TimelinePoint[]> => {
  const { data } = await api.get<{ success: boolean; data: TimelinePoint[] }>(
    "/analytics/timeline",
    { params: { days } }
  );
  return data.data;
};

export const fetchRiskDistribution = async (): Promise<RiskDistribution> => {
  const { data } = await api.get<{ success: boolean; data: RiskDistribution }>(
    "/analytics/risk-distribution"
  );
  return data.data;
};

export const fetchFalsePositiveAnalysis =
  async (): Promise<FalsePositiveAnalysis> => {
    const { data } = await api.get<{
      success: boolean;
      data: FalsePositiveAnalysis;
    }>("/analytics/false-positive-analysis");
    return data.data;
  };

export const fetchTransactions = async (
  params: {
    risk_level?: string;
    offset?: number;
    limit?: number;
  } = {}
): Promise<PaginatedResponse<Transaction>> => {
  const { data } = await api.get("/transactions", { params });
  return data;
};

export const fetchTransaction = async (
  id: number
): Promise<Transaction> => {
  const { data } = await api.get<{ success: boolean; data: Transaction }>(
    `/transactions/${id}`
  );
  return data.data;
};

export const fetchAlerts = async (
  params: {
    status?: string;
    risk_level?: string;
    offset?: number;
    limit?: number;
  } = {}
): Promise<PaginatedResponse<Alert>> => {
  const { data } = await api.get("/alerts", { params });
  return data;
};

export const updateAlertStatus = async (
  alertId: number,
  status: string
): Promise<void> => {
  await api.put(`/alerts/${alertId}/status`, { status });
};

export const fetchAlertStats = async (): Promise<AlertStats> => {
  const { data } = await api.get<{ success: boolean; data: AlertStats }>(
    "/alerts/stats"
  );
  return data.data;
};

export default api;
