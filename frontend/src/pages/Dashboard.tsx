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
    <div className="gradient-border rounded-2xl p-6">
      <div className="flex items-center justify-between">
        <div className="skeleton size-11 rounded-xl" />
        <div className="skeleton h-5 w-14 rounded-full" />
      </div>
      <div className="mt-5 space-y-2.5">
        <div className="skeleton h-9 w-28 rounded-lg" />
        <div className="skeleton h-4 w-36 rounded-lg" />
      </div>
    </div>
  );
}

function SkeletonChart() {
  return (
    <div className="glass-card rounded-2xl p-6">
      <div className="skeleton mb-5 h-5 w-44 rounded-lg" />
      <div className="skeleton h-[300px] w-full rounded-xl" />
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card rounded-xl border border-slate-700/30 px-4 py-3 shadow-2xl">
        <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">{label}</p>
        {payload.map((entry: any, i: number) => (
          <p key={i} className="text-[13px]" style={{ color: entry.color }}>
            {entry.name}: <span className="font-bold tabular-nums">{entry.value.toLocaleString("en-IN")}</span>
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
        <div className="flex items-center gap-4">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-xl shadow-indigo-500/20">
            <Shield className="size-6 text-white" />
          </div>
          <div>
            <h2 className="text-[26px] font-bold tracking-tight text-white leading-tight">Dashboard</h2>
            <p className="mt-0.5 text-[13px] text-slate-400 font-medium">
              Real-time fraud monitoring overview
            </p>
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
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

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Transactions"
          value={stats?.total_transactions?.toLocaleString("en-IN") || "—"}
          icon={<Activity className="size-5 text-white" />}
          color="indigo"
        />
        <StatCard
          label="Flagged Transactions"
          value={stats?.flagged_transactions?.toLocaleString("en-IN") || "—"}
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
          value={`₹${stats?.potential_savings?.toLocaleString("en-IN") || "—"}`}
          icon={<IndianRupee className="size-5 text-white" />}
          color="emerald"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="glass-card animate-slide-up rounded-2xl p-6" style={{ animationDelay: "100ms" }}>
          <div className="mb-5 flex items-center justify-between">
            <h3 className="text-[14px] font-semibold text-slate-200 tracking-tight">
              Fraud Attempts Timeline
            </h3>
            <span className="rounded-full bg-indigo-500/10 px-3 py-1 text-[11px] font-semibold tracking-wide text-indigo-400">
              30 days
            </span>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeline || []}>
              <defs>
                <linearGradient id="gradientTotal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradientFlagged" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ef4444" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(51, 65, 85, 0.2)" />
              <XAxis
                dataKey="date"
                stroke="#475569"
                fontSize={11}
                fontWeight={500}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => format(new Date(v), "MMM d")}
              />
              <YAxis
                stroke="#475569"
                fontSize={11}
                fontWeight={500}
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
                activeDot={{ r: 5, fill: "#6366f1", stroke: "#030712", strokeWidth: 2.5 }}
              />
              <Line
                type="monotone"
                dataKey="flagged"
                stroke="#ef4444"
                strokeWidth={2.5}
                name="Flagged"
                dot={false}
                activeDot={{ r: 5, fill: "#ef4444", stroke: "#030712", strokeWidth: 2.5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card animate-slide-up rounded-2xl p-6" style={{ animationDelay: "200ms" }}>
          <div className="mb-5 flex items-center justify-between">
            <h3 className="text-[14px] font-semibold text-slate-200 tracking-tight">
              Risk Distribution
            </h3>
            <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold tracking-wide text-emerald-400 flex items-center gap-1.5">
              <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse-slow" />
              Live
            </span>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={distData}>
              <defs>
                <linearGradient id="barGradLow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0.5} />
                </linearGradient>
                <linearGradient id="barGradMedium" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.5} />
                </linearGradient>
                <linearGradient id="barGradHigh" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f97316" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#f97316" stopOpacity={0.5} />
                </linearGradient>
                <linearGradient id="barGradCritical" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ef4444" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#ef4444" stopOpacity={0.5} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(51, 65, 85, 0.2)" />
              <XAxis
                dataKey="level"
                stroke="#475569"
                fontSize={11}
                fontWeight={500}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#475569"
                fontSize={11}
                fontWeight={500}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="count"
                radius={[8, 8, 0, 0]}
                fill="url(#barGradLow)"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-card animate-slide-up rounded-2xl p-6" style={{ animationDelay: "300ms" }}>
        <div className="mb-5 flex items-center justify-between">
          <h3 className="text-[14px] font-semibold text-slate-200 tracking-tight">
            Recent Alerts
          </h3>
          <a
            href="/alerts"
            className="flex items-center gap-1.5 text-[12px] font-semibold text-indigo-400 transition-colors hover:text-indigo-300"
          >
            View all <ArrowRight className="size-3.5" />
          </a>
        </div>
        <div className="space-y-2">
          {(alerts?.data || []).map((alert, i) => (
            <div
              key={alert.id}
              className="glass-card group flex items-center justify-between rounded-xl px-4 py-3.5 transition-all duration-200 hover:bg-slate-800/40"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              <div className="flex items-center gap-4">
                <RiskBadge level={alert.risk_level} score={alert.risk_score} />
                <div>
                  <p className="text-[13px] font-semibold text-slate-200">
                    Transaction #{alert.transaction_id}
                  </p>
                  <p className="mt-0.5 text-[12px] text-slate-500">
                    {alert.explanation?.[0]?.description || "No details"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide ${
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
            <div className="py-16 text-center">
              <Shield className="mx-auto mb-4 size-12 text-slate-700/60" />
              <p className="text-[14px] text-slate-500 font-medium">
                No alerts yet. Send some transactions to get started.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
