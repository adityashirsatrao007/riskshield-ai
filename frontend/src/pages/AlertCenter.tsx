import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAlerts, updateAlertStatus, fetchAlertStats } from "../lib/api";
import { RiskBadge } from "../components/RiskBadge";
import { useToast } from "../components/Toast";
import { format } from "date-fns";
import { Bell, CheckCircle, XCircle, Eye } from "lucide-react";

export default function AlertCenter() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [statusFilter, setStatusFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");

  const { data: alerts, isLoading } = useQuery({
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
      toast("Alert updated", "success");
    },
    onError: (error: Error) => {
      toast(`Failed to update alert: ${error.message}`, "error");
    },
  });

  const alertList = alerts?.data || [];

  const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  const sorted = [...alertList].sort(
    (a, b) =>
      (priorityOrder[a.risk_level] ?? 4) - (priorityOrder[b.risk_level] ?? 4)
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Alert Center</h2>
        <p className="text-sm text-slate-400">
          Review and manage fraud alerts
        </p>
      </div>

      {stats && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {["open", "acknowledged", "dismissed", "resolved"].map((s) => (
            <div
              key={s}
              className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 text-center"
            >
              <p className="text-2xl font-bold text-white">
                {stats.by_status[s] || 0}
              </p>
              <p className="text-xs text-slate-400 capitalize">{s}</p>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-brand-500 focus:outline-none"
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
          className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-brand-500 focus:outline-none"
        >
          <option value="">All Risk Levels</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-sm text-slate-500">Loading...</div>
      ) : sorted.length === 0 ? (
        <div className="text-center py-12 text-sm text-slate-500">
          No alerts found. All clear!
        </div>
      ) : (
        <div className="space-y-4">
          {sorted.map((alert) => (
            <div
              key={alert.id}
              className="rounded-xl border border-slate-800 bg-slate-900/50 p-5"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div
                    className={`mt-1 rounded-lg p-2 ${
                      alert.risk_level === "critical"
                        ? "bg-red-500/15"
                        : alert.risk_level === "high"
                        ? "bg-orange-500/15"
                        : alert.risk_level === "medium"
                        ? "bg-amber-500/15"
                        : "bg-emerald-500/15"
                    }`}
                  >
                    <Bell
                      className={`size-5 ${
                        alert.risk_level === "critical"
                          ? "text-red-400"
                          : alert.risk_level === "high"
                          ? "text-orange-400"
                          : alert.risk_level === "medium"
                          ? "text-amber-400"
                          : "text-emerald-400"
                      }`}
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
                      {alert.explanation?.map((exp, i) => (
                        <p key={i} className="text-sm text-slate-300">
                          <span className="font-medium text-slate-200">
                            {exp.feature}
                          </span>
                          {" = "}
                          {exp.value} (importance: {exp.importance})
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
                        className="rounded-lg bg-brand-600/15 px-3 py-1.5 text-xs font-medium text-brand-400 hover:bg-brand-600/25"
                      >
                        <Eye className="mr-1 inline size-3" />
                        Acknowledge
                      </button>
                      <button
                        onClick={() =>
                          mutation.mutate({ id: alert.id, status: "resolved" })
                        }
                        className="rounded-lg bg-emerald-600/15 px-3 py-1.5 text-xs font-medium text-emerald-400 hover:bg-emerald-600/25"
                      >
                        <CheckCircle className="mr-1 inline size-3" />
                        Resolve
                      </button>
                      <button
                        onClick={() =>
                          mutation.mutate({ id: alert.id, status: "dismissed" })
                        }
                        className="rounded-lg bg-slate-600/15 px-3 py-1.5 text-xs font-medium text-slate-400 hover:bg-slate-600/25"
                      >
                        <XCircle className="mr-1 inline size-3" />
                        Dismiss
                      </button>
                    </>
                  )}
                  {alert.status !== "open" && (
                    <span className="text-xs text-slate-500 capitalize px-2 py-1">
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
