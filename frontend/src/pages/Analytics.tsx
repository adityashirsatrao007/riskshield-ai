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

const COLORS = ["#10b981", "#f59e0b", "#f97316", "#ef4444"];

export default function Analytics() {
  const { data: timeline } = useQuery({
    queryKey: ["timeline-analytics"],
    queryFn: () => fetchTimeline(30),
  });

  const { data: distribution } = useQuery({
    queryKey: ["risk-dist-analytics"],
    queryFn: fetchRiskDistribution,
  });

  const { data: fpAnalysis } = useQuery({
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

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white">Analytics</h2>
        <p className="text-sm text-slate-400">
          Deep dive into fraud patterns and model performance
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="mb-4 text-sm font-semibold text-slate-200">
            Fraud Rate Over Time
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
                dataKey="avg_score"
                stroke="#8b5cf6"
                strokeWidth={2}
                name="Avg Risk Score"
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
            Risk Level Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={distData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={4}
                dataKey="value"
              >
                {distData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 flex justify-center gap-4">
            {distData.map((d) => (
              <div key={d.name} className="flex items-center gap-1.5 text-xs">
                <span
                  className="size-2 rounded-full"
                  style={{ backgroundColor: d.color }}
                />
                <span className="text-slate-400">{d.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h3 className="mb-4 text-sm font-semibold text-slate-200">
          False Positive Cost Analysis
        </h3>
        {fpAnalysis && (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-white">
                ₹{fpAnalysis.estimated_savings.toLocaleString()}
              </p>
              <p className="mt-1 text-sm text-slate-400">Fraud Prevented</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-amber-400">
                ₹{fpAnalysis.estimated_fp_cost.toLocaleString()}
              </p>
              <p className="mt-1 text-sm text-slate-400">
                False Positive Cost
              </p>
            </div>
            <div className="text-center">
              <p
                className={`text-3xl font-bold ${
                  fpAnalysis.net_benefit >= 0
                    ? "text-emerald-400"
                    : "text-red-400"
                }`}
              >
                ₹{fpAnalysis.net_benefit.toLocaleString()}
              </p>
              <p className="mt-1 text-sm text-slate-400">Net Benefit</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-brand-400">
                {fpAnalysis.total_flagged}
              </p>
              <p className="mt-1 text-sm text-slate-400">Total Flagged</p>
            </div>
          </div>
        )}
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h3 className="mb-4 text-sm font-semibold text-slate-200">
          Transaction Volume by Day
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={timeline || []}>
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
            <Bar dataKey="total" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Total" />
            <Bar
              dataKey="flagged"
              fill="#ef4444"
              radius={[4, 4, 0, 0]}
              name="Flagged"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
