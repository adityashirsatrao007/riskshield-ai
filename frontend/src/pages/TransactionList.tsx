import { useState, Fragment } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchTransactions } from "../lib/api";
import { RiskBadge } from "../components/RiskBadge";
import { format } from "date-fns";
import {
  ChevronDown,
  Search,
  Filter,
  CreditCard,
  Globe,
  Store,
  Clock,
} from "lucide-react";
import { clsx } from "clsx";

export default function TransactionList() {
  const [riskFilter, setRiskFilter] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["transactions", riskFilter, page],
    queryFn: () =>
      fetchTransactions({
        risk_level: riskFilter || undefined,
        offset: page * limit,
        limit,
      }),
  });

  const transactions = data?.data || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / limit);

  const filtered = search
    ? transactions.filter(
        (t) =>
          t.transaction_id.toLowerCase().includes(search.toLowerCase()) ||
          t.customer_id.toLowerCase().includes(search.toLowerCase())
      )
    : transactions;

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg shadow-blue-500/20">
            <Filter className="size-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Transactions</h2>
            <p className="text-sm text-slate-400">
              All scored transactions with risk analysis
            </p>
          </div>
        </div>
      </div>

      <div className="glass-card flex flex-wrap items-center gap-4 rounded-2xl p-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ID or customer..."
            className="w-full rounded-xl border border-slate-700/50 bg-slate-800/50 py-2.5 pl-10 pr-4 text-sm text-slate-200 placeholder-slate-500 backdrop-blur-sm focus:border-indigo-500/50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          />
        </div>
        <select
          value={riskFilter}
          onChange={(e) => {
            setRiskFilter(e.target.value);
            setPage(0);
          }}
          className="rounded-xl border border-slate-700/50 bg-slate-800/50 px-4 py-2.5 text-sm text-slate-200 backdrop-blur-sm focus:border-indigo-500/50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
        >
          <option value="">All Risk Levels</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      <div className="glass-card overflow-hidden rounded-2xl">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800/50 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
              <th className="px-5 py-4">Transaction</th>
              <th className="px-5 py-4">Amount</th>
              <th className="px-5 py-4">Customer</th>
              <th className="px-5 py-4">Risk</th>
              <th className="px-5 py-4">Status</th>
              <th className="px-5 py-4">Time</th>
              <th className="w-8 px-5 py-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {isLoading ? (
              <tr>
                <td
                  colSpan={7}
                  className="px-5 py-16 text-center text-sm text-slate-500"
                >
                  <div className="flex items-center justify-center gap-2">
                    <div className="size-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
                    Loading transactions...
                  </div>
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td
                  colSpan={7}
                  className="px-5 py-16 text-center text-sm text-slate-500"
                >
                  No transactions found. Send some via the API to see them here.
                </td>
              </tr>
            ) : (
              filtered.map((txn, i) => (
                <Fragment key={txn.id}>
                  <tr
                    className={clsx(
                      "cursor-pointer transition-all duration-200 hover:bg-slate-800/30",
                      expandedId === txn.id && "bg-slate-800/20"
                    )}
                    style={{ animationDelay: `${i * 30}ms` }}
                    onClick={() =>
                      setExpandedId(expandedId === txn.id ? null : txn.id)
                    }
                  >
                    <td className="px-5 py-4">
                      <span className="font-mono text-sm text-slate-200">
                        {txn.transaction_id}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-sm font-semibold text-white">
                        ₹{txn.amount.toLocaleString()}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-400">
                      {txn.customer_id}
                    </td>
                    <td className="px-5 py-4">
                      <RiskBadge
                        level={txn.risk_level}
                        score={txn.risk_score}
                      />
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={clsx(
                          "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
                          txn.is_flagged
                            ? "bg-red-500/10 text-red-400"
                            : "bg-emerald-500/10 text-emerald-400"
                        )}
                      >
                        <span
                          className={clsx(
                            "size-1.5 rounded-full",
                            txn.is_flagged ? "bg-red-400" : "bg-emerald-400"
                          )}
                        />
                        {txn.is_flagged ? "Flagged" : "Clean"}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-xs text-slate-500">
                      {format(new Date(txn.created_at), "MMM d, HH:mm")}
                    </td>
                    <td className="px-5 py-4">
                      <ChevronDown
                        className={clsx(
                          "size-4 text-slate-500 transition-transform duration-200",
                          expandedId === txn.id && "rotate-180"
                        )}
                      />
                    </td>
                  </tr>
                  {expandedId === txn.id && (
                    <tr>
                      <td
                        colSpan={7}
                        className="border-t border-slate-800/30 bg-slate-800/10 px-8 py-5"
                      >
                        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                          <div className="flex items-center gap-3 rounded-xl bg-slate-800/30 p-3">
                            <CreditCard className="size-8 text-slate-600" />
                            <div>
                              <p className="text-[11px] text-slate-500">
                                Card Type
                              </p>
                              <p className="text-sm font-medium text-slate-200">
                                {txn.card_type}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3 rounded-xl bg-slate-800/30 p-3">
                            <Globe className="size-8 text-slate-600" />
                            <div>
                              <p className="text-[11px] text-slate-500">
                                International
                              </p>
                              <p className="text-sm font-medium text-slate-200">
                                {txn.is_international ? "Yes" : "No"}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3 rounded-xl bg-slate-800/30 p-3">
                            <Store className="size-8 text-slate-600" />
                            <div>
                              <p className="text-[11px] text-slate-500">
                                Merchant
                              </p>
                              <p className="text-sm font-medium text-slate-200">
                                {txn.merchant_id}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3 rounded-xl bg-slate-800/30 p-3">
                            <Clock className="size-8 text-slate-600" />
                            <div>
                              <p className="text-[11px] text-slate-500">
                                Created
                              </p>
                              <p className="text-sm font-medium text-slate-200">
                                {format(
                                  new Date(txn.created_at),
                                  "MMM d, HH:mm"
                                )}
                              </p>
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="glass-card flex items-center justify-between rounded-2xl px-5 py-4">
          <p className="text-sm text-slate-400">
            Showing {page * limit + 1}–
            {Math.min((page + 1) * limit, total)} of {total}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="rounded-xl border border-slate-700/50 bg-slate-800/50 px-4 py-2 text-sm text-slate-300 backdrop-blur-sm transition-all hover:bg-slate-700/50 disabled:opacity-40"
            >
              Prev
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="rounded-xl border border-slate-700/50 bg-slate-800/50 px-4 py-2 text-sm text-slate-300 backdrop-blur-sm transition-all hover:bg-slate-700/50 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
