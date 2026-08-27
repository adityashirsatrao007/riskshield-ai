import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAlerts, updateAlertStatus, fetchAlertStats } from "../lib/api";
import { RiskBadge } from "../components/RiskBadge";
import { format } from "date-fns";
import {
  Bell,
  Eye,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Shield,
  Filter,
} from "lucide-react";
import { clsx } from "clsx";

export default function AlertCenter() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["alerts", statusFilter, riskFilter],
    queryFn: () =>
      fetchAlerts({
        status: statusFilter || undefined,
        risk_level: riskFilter || undefined,
        limit: 50,
      }),
  });

  const { data: stats } = useQuery({
    queryKey: ["alert-stats"],
    queryFn: fetchAlertStats,
  });

  const mutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      updateAlertStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["alert-stats"] });
    },
  });

  const alerts = data?.data || [];
  const sorted = [...alerts].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 shadow-lg shadow-amber-500/20">
            <AlertTriangle className="size-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Alert Center</h2>
            <p className="text-sm text-slate-400">
              Manage and respond to fraud alerts
            </p>
          </div>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {["open", "acknowledged", "dismissed", "resolved"].map((status) => (
            <div
              key={status}
              className="glass-card rounded-xl p-4 text-center transition-all hover:scale-[1.02]"
            >
              <p className="text-2xl font-bold text-white">
                {stats.by_status?.[status] || 0}
              </p>
              <p className="mt-1 text-xs capitalize text-slate-400">
                {status}
              </p>
            </div>
          ))}
        </div>
      )}

      <div className="glass-card flex flex-wrap items-center gap-4 rounded-2xl p-4">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Filter className="size-4" />
          Filters
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-slate-700/50 bg-slate-800/50 px-4 py-2.5 text-sm text-slate-200 backdrop-blur-sm focus:border-indigo-500/50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="dismissed">Dismissed</option>
          <option value="resolved">Resolved</option>
        </select>
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          className="rounded-xl border border-slate-700/50 bg-slate-800/50 px-4 py-2.5 text-sm text-slate-200 backdrop-blur-sm focus:border-indigo-500/50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
        >
          <option value="">All Risk Levels</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <div className="flex items-center gap-3 text-sm text-slate-400">
            <div className="size-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            Loading alerts...
          </div>
        </div>
      ) : sorted.length === 0 ? (
        <div className="glass-card rounded-2xl py-16 text-center">
          <Shield className="mx-auto mb-3 size-12 text-slate-700" />
          <p className="text-sm text-slate-500">No alerts found. All clear!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sorted.map((alert, i) => (
            <div
              key={alert.id}
              className="glass-card animate-slide-up group rounded-2xl p-5 transition-all duration-200 hover:bg-slate-800/30"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div
                    className={clsx(
                      "mt-1 flex size-10 items-center justify-center rounded-xl",
                      alert.risk_level === "critical"
                        ? "bg-red-500/15 shadow-lg shadow-red-500/10"
                        : alert.risk_level === "high"
                        ? "bg-orange-500/15 shadow-lg shadow-orange-500/10"
                        : alert.risk_level === "medium"
                        ? "bg-amber-500/15 shadow-lg shadow-amber-500/10"
                        : "bg-emerald-500/15 shadow-lg shadow-emerald-500/10"
                    )}
                  >
                    <Bell
                      className={clsx(
                        "size-5",
                        alert.risk_level === "critical"
                          ? "text-red-400"
                          : alert.risk_level === "high"
                          ? "text-orange-400"
                          : alert.risk_level === "medium"
                          ? "text-amber-400"
                          : "text-emerald-400"
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center gap-3">
                      <RiskBadge
                        level={alert.risk_level}
                        score={alert.risk_score}
                      />
                      <span className="text-xs text-slate-500">
                        {format(
                          new Date(alert.created_at),
                          "MMM d, yyyy HH:mm"
                        )}
                      </span>
                    </div>
                    <div className="mt-3 space-y-1.5">
                      {alert.explanation?.map((exp, j) => (
                        <p key={j} className="text-sm text-slate-300">
                          <span className="font-medium text-slate-200">
                            {exp.feature}
                          </span>{" "}
                          = {exp.value}{" "}
                          <span className="text-slate-500">
                            (importance: {exp.importance})
                          </span>
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  {alert.status === "open" && (
                    <>
                      <button
                        onClick={() =>
                          mutation.mutate({
                            id: alert.id,
                            status: "acknowledged",
                          })
                        }
                        className="rounded-xl bg-indigo-500/10 px-3 py-1.5 text-xs font-medium text-indigo-400 transition-all hover:bg-indigo-500/20"
                      >
                        <Eye className="mr-1 inline size-3" />
                        Acknowledge
                      </button>
                      <button
                        onClick={() =>
                          mutation.mutate({
                            id: alert.id,
                            status: "resolved",
                          })
                        }
                        className="rounded-xl bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-400 transition-all hover:bg-emerald-500/20"
                      >
                        <CheckCircle className="mr-1 inline size-3" />
                        Resolve
                      </button>
                      <button
                        onClick={() =>
                          mutation.mutate({
                            id: alert.id,
                            status: "dismissed",
                          })
                        }
                        className="rounded-xl bg-slate-500/10 px-3 py-1.5 text-xs font-medium text-slate-400 transition-all hover:bg-slate-500/20"
                      >
                        <XCircle className="mr-1 inline size-3" />
                        Dismiss
                      </button>
                    </>
                  )}
                  {alert.status !== "open" && (
                    <span className="rounded-full bg-slate-500/10 px-3 py-1 text-xs font-medium text-slate-400 capitalize">
                      {alert.status}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
