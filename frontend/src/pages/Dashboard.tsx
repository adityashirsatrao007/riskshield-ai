import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import {
  Activity,
  AlertTriangle,
  Percent,
  IndianRupee,
} from "lucide-react";
import {
  fetchDashboard,
  fetchTimeline,
  fetchRiskDistribution,
  fetchAlerts,
} from "../lib/api";
import { StatCard } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";
import { format } from "date-fns";

const RISK_COLORS: Record<string, string> = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#f97316",
  critical: "#ef4444",
};

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboard,
  });

  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ["timeline"],
    queryFn: () => fetchTimeline(30),
  });

  const { data: distribution, isLoading: distLoading } = useQuery({
    queryKey: ["risk-distribution"],
    queryFn: fetchRiskDistribution,
  });

  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ["alerts-recent"],
    queryFn: () => fetchAlerts({ limit: 10 }),
  });

  const distData = distribution
    ? Object.entries(distribution).map(([level, count]) => ({
        level: level.charAt(0).toUpperCase() + level.slice(1),
        count,
        fill: RISK_COLORS[level] || "#64748b",
      }))
    : [];

  const isLoading = statsLoading || timelineLoading || distLoading || alertsLoading;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
        <p className="text-sm text-slate-400">
          Real-time fraud monitoring overview
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-sm text-slate-400">Loading dashboard data...</div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Transactions"
          value={stats?.total_transactions?.toLocaleString() || "—"}
          icon={<Activity className="size-5 text-brand-400" />}
        />
        <StatCard
          label="Flagged Transactions"
          value={stats?.flagged_transactions?.toLocaleString() || "—"}
          icon={<AlertTriangle className="size-5 text-amber-400" />}
        />
        <StatCard
          label="Fraud Rate"
          value={stats?.fraud_rate?.toFixed(1) || "—"}
          suffix="%"
          icon={<Percent className="size-5 text-red-400" />}
        />
        <StatCard
          label="Potential Savings"
          value={`₹${stats?.potential_savings?.toLocaleString() || "—"}`}
          icon={<IndianRupee className="size-5 text-emerald-400" />}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="mb-4 text-sm font-semibold text-slate-200">
            Fraud Attempts Timeline
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeline || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="date"
                stroke="#64748b"
                fontSize={11}
                tickFormatter={(v) => format(new Date(v), "MMM d")}
              />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Line
                type="monotone"
                dataKey="total"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Total"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="flagged"
                stroke="#ef4444"
                strokeWidth={2}
                name="Flagged"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="mb-4 text-sm font-semibold text-slate-200">
            Risk Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={distData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="level" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h3 className="mb-4 text-sm font-semibold text-slate-200">
          Recent Alerts
        </h3>
        <div className="space-y-3">
          {(alerts?.data || []).map((alert) => (
            <div
              key={alert.id}
              className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-800/30 px-4 py-3"
            >
              <div className="flex items-center gap-4">
                <RiskBadge level={alert.risk_level} score={alert.risk_score} />
                <div>
                  <p className="text-sm text-slate-200">
                    Transaction #{alert.transaction_id}
                  </p>
                  <p className="text-xs text-slate-500">
                    {alert.explanation?.[0]?.description || "No details"}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span
                  className={`text-xs font-medium ${
                    alert.status === "open"
                      ? "text-amber-400"
                      : alert.status === "resolved"
                      ? "text-emerald-400"
                      : "text-slate-400"
                  }`}
                >
                  {alert.status}
                </span>
              </div>
            </div>
          ))}
          {(!alerts?.data || alerts.data.length === 0) && (
            <p className="text-center text-sm text-slate-500 py-8">
              No alerts yet. Send some transactions to get started.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
