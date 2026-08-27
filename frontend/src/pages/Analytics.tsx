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
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  fetchTimeline,
  fetchRiskDistribution,
  fetchFalsePositiveAnalysis,
} from "../lib/api";
import { format } from "date-fns";
import { BarChart3, TrendingUp, IndianRupee } from "lucide-react";

const COLORS = ["#10b981", "#f59e0b", "#f97316", "#ef4444"];

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

export default function Analytics() {
  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ["timeline-analytics"],
    queryFn: () => fetchTimeline(30),
  });

  const { data: distribution, isLoading: distLoading } = useQuery({
    queryKey: ["risk-dist-analytics"],
    queryFn: fetchRiskDistribution,
  });

  const { data: fpAnalysis, isLoading: fpLoading } = useQuery({
    queryKey: ["fp-analysis"],
    queryFn: fetchFalsePositiveAnalysis,
  });

  const distData = distribution
    ? Object.entries(distribution).map(([level, count], i) => ({
        name: level.charAt(0).toUpperCase() + level.slice(1),
        value: count,
        color: COLORS[i],
      }))
    : [];

  const isLoading = timelineLoading || distLoading || fpLoading;

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg shadow-purple-500/20">
            <BarChart3 className="size-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Analytics</h2>
            <p className="text-sm text-slate-400">
              Deep dive into fraud patterns and model performance
            </p>
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <div className="flex items-center gap-3 text-sm text-slate-400">
            <div className="size-4 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
            Loading analytics...
          </div>
        </div>
      )}

      {fpAnalysis && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="gradient-border glow-emerald rounded-2xl p-5 transition-all hover:scale-[1.02]">
            <div className="mb-3 flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 shadow-lg">
              <IndianRupee className="size-5 text-white" />
            </div>
            <p className="text-2xl font-bold text-white">
              ₹{fpAnalysis.estimated_savings.toLocaleString()}
            </p>
            <p className="mt-1 text-sm text-slate-400">Fraud Prevented</p>
          </div>
          <div className="gradient-border glow-amber rounded-2xl p-5 transition-all hover:scale-[1.02]">
            <div className="mb-3 flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 shadow-lg">
              <IndianRupee className="size-5 text-white" />
            </div>
            <p className="text-2xl font-bold text-amber-400">
              ₹{fpAnalysis.estimated_fp_cost.toLocaleString()}
            </p>
            <p className="mt-1 text-sm text-slate-400">
              False Positive Cost
            </p>
          </div>
          <div className="gradient-border glow-purple rounded-2xl p-5 transition-all hover:scale-[1.02]">
            <div className="mb-3 flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg">
              <TrendingUp className="size-5 text-white" />
            </div>
            <p
              className={`text-2xl font-bold ${
                fpAnalysis.net_benefit >= 0
                  ? "text-emerald-400"
                  : "text-red-400"
              }`}
            >
              ₹{fpAnalysis.net_benefit.toLocaleString()}
            </p>
            <p className="mt-1 text-sm text-slate-400">Net Benefit</p>
          </div>
          <div className="gradient-border glow-blue rounded-2xl p-5 transition-all hover:scale-[1.02]">
            <div className="mb-3 flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-blue-500 shadow-lg">
              <BarChart3 className="size-5 text-white" />
            </div>
            <p className="text-2xl font-bold text-brand-400">
              {fpAnalysis.total_flagged}
            </p>
            <p className="mt-1 text-sm text-slate-400">Total Flagged</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="glass-card animate-slide-up rounded-2xl p-6" style={{ animationDelay: "100ms" }}>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200">
              Fraud Rate Over Time
            </h3>
            <span className="rounded-full bg-purple-500/10 px-2.5 py-0.5 text-[11px] font-medium text-purple-400">
              30 days
            </span>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeline || []}>
              <defs>
                <linearGradient id="gradPurple" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#a78bfa" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#a78bfa" stopOpacity={0} />
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
              <YAxis stroke="#475569" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="avg_score"
                stroke="#a78bfa"
                strokeWidth={2.5}
                name="Avg Risk Score"
                dot={false}
                activeDot={{ r: 5, fill: "#a78bfa", stroke: "#030712", strokeWidth: 2 }}
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
              Risk Level Distribution
            </h3>
            <span className="rounded-full bg-pink-500/10 px-2.5 py-0.5 text-[11px] font-medium text-pink-400">
              Live
            </span>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={distData}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={110}
                paddingAngle={4}
                dataKey="value"
                stroke="none"
              >
                {distData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 flex justify-center gap-4">
            {distData.map((d) => (
              <div key={d.name} className="flex items-center gap-1.5 text-xs">
                <span
                  className="size-2 rounded-full shadow-lg"
                  style={{ backgroundColor: d.color }}
                />
                <span className="text-slate-400">{d.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="glass-card animate-slide-up rounded-2xl p-6" style={{ animationDelay: "300ms" }}>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">
            Transaction Volume by Day
          </h3>
          <span className="rounded-full bg-blue-500/10 px-2.5 py-0.5 text-[11px] font-medium text-blue-400">
            Daily
          </span>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={timeline || []}>
            <defs>
              <linearGradient id="gradBlue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#818cf8" stopOpacity={0.9} />
                <stop offset="100%" stopColor="#6366f1" stopOpacity={0.6} />
              </linearGradient>
              <linearGradient id="gradRed" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f87171" stopOpacity={0.9} />
                <stop offset="100%" stopColor="#ef4444" stopOpacity={0.6} />
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
            <YAxis stroke="#475569" fontSize={11} tickLine={false} axisLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="total"
              fill="url(#gradBlue)"
              radius={[6, 6, 0, 0]}
              name="Total"
            />
            <Bar
              dataKey="flagged"
              fill="url(#gradRed)"
              radius={[6, 6, 0, 0]}
              name="Flagged"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
