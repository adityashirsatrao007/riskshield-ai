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
  Shield,
  ArrowRight,
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

function SkeletonCard() {
  return (
    <div className="gradient-border rounded-2xl p-5">
      <div className="flex items-center justify-between">
        <div className="skeleton size-10 rounded-xl" />
        <div className="skeleton h-5 w-12 rounded-full" />
      </div>
      <div className="mt-4 space-y-2">
        <div className="skeleton h-8 w-24 rounded-lg" />
        <div className="skeleton h-4 w-32 rounded-lg" />
      </div>
    </div>
  );
}

function SkeletonChart() {
  return (
    <div className="glass-card rounded-2xl p-6">
      <div className="skeleton mb-4 h-5 w-40 rounded-lg" />
      <div className="skeleton h-[300px] w-full rounded-xl" />
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card rounded-xl border border-slate-700/50 px-4 py-3 shadow-2xl">
        <p className="mb-1 text-xs font-medium text-slate-300">{label}</p>
        {payload.map((entry: any, i: number) => (
          <p key={i} className="text-xs" style={{ color: entry.color }}>
            {entry.name}: <span className="font-semibold">{entry.value}</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
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
      <div className="animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20">
            <Shield className="size-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Dashboard</h2>
            <p className="text-sm text-slate-400">
              Real-time fraud monitoring overview
            </p>
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <SkeletonChart />
            <SkeletonChart />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Transactions"
          value={stats?.total_transactions?.toLocaleString() || "—"}
          icon={<Activity className="size-5 text-white" />}
          color="indigo"
        />
        <StatCard
          label="Flagged Transactions"
          value={stats?.flagged_transactions?.toLocaleString() || "—"}
          icon={<AlertTriangle className="size-5 text-white" />}
          color="amber"
        />
        <StatCard
          label="Fraud Rate"
          value={stats?.fraud_rate?.toFixed(1) || "—"}
          suffix="%"
          icon={<Percent className="size-5 text-white" />}
          color="red"
        />
        <StatCard
          label="Potential Savings"
          value={`₹${stats?.potential_savings?.toLocaleString() || "—"}`}
          icon={<IndianRupee className="size-5 text-white" />}
          color="emerald"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="glass-card animate-slide-up rounded-2xl p-6" style={{ animationDelay: "100ms" }}>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200">
              Fraud Attempts Timeline
            </h3>
            <span className="rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-[11px] font-medium text-indigo-400">
              30 days
            </span>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeline || []}>
              <defs>
                <linearGradient id="gradientTotal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradientFlagged" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(51, 65, 85, 0.3)" />
              <XAxis
                dataKey="date"
                stroke="#475569"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => format(new Date(v), "MMM d")}
              />
              <YAxis
                stroke="#475569"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="total"
                stroke="#6366f1"
                strokeWidth={2.5}
                name="Total"
                dot={false}
                activeDot={{ r: 5, fill: "#6366f1", stroke: "#030712", strokeWidth: 2 }}
              />
              <Line
                type="monotone"
                dataKey="flagged"
                stroke="#ef4444"
                strokeWidth={2.5}
                name="Flagged"
                dot={false}
                activeDot={{ r: 5, fill: "#ef4444", stroke: "#030712", strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card animate-slide-up rounded-2xl p-6" style={{ animationDelay: "200ms" }}>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200">
              Risk Distribution
            </h3>
            <span className="rounded-full bg-purple-500/10 px-2.5 py-0.5 text-[11px] font-medium text-purple-400">
              Live
            </span>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={distData}>
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#818cf8" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0.6} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(51, 65, 85, 0.3)" />
              <XAxis
                dataKey="level"
                stroke="#475569"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#475569"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="count"
                radius={[8, 8, 0, 0]}
                fill="url(#barGradient)"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-card animate-slide-up rounded-2xl p-6" style={{ animationDelay: "300ms" }}>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">
            Recent Alerts
          </h3>
          <a
            href="/alerts"
            className="flex items-center gap-1 text-xs font-medium text-indigo-400 transition-colors hover:text-indigo-300"
          >
            View all <ArrowRight className="size-3" />
          </a>
        </div>
        <div className="space-y-3">
          {(alerts?.data || []).map((alert, i) => (
            <div
              key={alert.id}
              className="glass-card group flex items-center justify-between rounded-xl px-4 py-3 transition-all duration-200 hover:bg-slate-800/50"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <div className="flex items-center gap-4">
                <RiskBadge level={alert.risk_level} score={alert.risk_score} />
                <div>
                  <p className="text-sm font-medium text-slate-200">
                    Transaction #{alert.transaction_id}
                  </p>
                  <p className="text-xs text-slate-500">
                    {alert.explanation?.[0]?.description || "No details"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
                    alert.status === "open"
                      ? "bg-amber-500/10 text-amber-400"
                      : alert.status === "resolved"
                      ? "bg-emerald-500/10 text-emerald-400"
                      : "bg-slate-500/10 text-slate-400"
                  }`}
                >
                  {alert.status}
                </span>
                <ArrowRight className="size-4 text-slate-600 transition-all group-hover:translate-x-1 group-hover:text-slate-400" />
              </div>
            </div>
          ))}
          {(!alerts?.data || alerts.data.length === 0) && (
            <div className="py-12 text-center">
              <Shield className="mx-auto mb-3 size-10 text-slate-700" />
              <p className="text-sm text-slate-500">
                No alerts yet. Send some transactions to get started.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
