import { useState, Fragment } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchTransactions } from "../lib/api";
import { RiskBadge } from "../components/RiskBadge";
import { format } from "date-fns";
import { ChevronDown, ChevronUp, Search } from "lucide-react";

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
      <div>
        <h2 className="text-2xl font-bold text-white">Transactions</h2>
        <p className="text-sm text-slate-400">
          All scored transactions with risk analysis
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ID or customer..."
            className="w-full rounded-lg border border-slate-700 bg-slate-800 py-2 pl-10 pr-4 text-sm text-slate-200 placeholder-slate-500 focus:border-brand-500 focus:outline-none"
          />
        </div>
        <select
          value={riskFilter}
          onChange={(e) => {
            setRiskFilter(e.target.value);
            setPage(0);
          }}
          className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-brand-500 focus:outline-none"
        >
          <option value="">All Risk Levels</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
              <th className="px-4 py-3">Transaction</th>
              <th className="px-4 py-3">Amount</th>
              <th className="px-4 py-3">Customer</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Time</th>
              <th className="px-4 py-3 w-8"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-sm text-slate-500">
                  Loading...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-sm text-slate-500">
                  No transactions found. Send some via the API to see them here.
                </td>
              </tr>
            ) : (
              filtered.map((txn) => (
                <Fragment key={txn.id}>
                  <tr
                    className="hover:bg-slate-800/50 cursor-pointer"
                    onClick={() =>
                      setExpandedId(expandedId === txn.id ? null : txn.id)
                    }
                  >
                    <td className="px-4 py-3 text-sm font-mono text-slate-200">
                      {txn.transaction_id}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-200">
                      ₹{txn.amount.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {txn.customer_id}
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge
                        level={txn.risk_level}
                        score={txn.risk_score}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs font-medium ${
                          txn.is_flagged
                            ? "text-red-400"
                            : "text-emerald-400"
                        }`}
                      >
                        {txn.is_flagged ? "Flagged" : "Clean"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {format(new Date(txn.created_at), "MMM d, HH:mm")}
                    </td>
                    <td className="px-4 py-3">
                      {expandedId === txn.id ? (
                        <ChevronUp className="size-4 text-slate-500" />
                      ) : (
                        <ChevronDown className="size-4 text-slate-500" />
                      )}
                    </td>
                  </tr>
                  {expandedId === txn.id && (
                    <tr>
                      <td colSpan={7} className="bg-slate-800/30 px-8 py-4">
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-slate-500">Card Type</span>
                            <p className="text-slate-200">{txn.card_type}</p>
                          </div>
                          <div>
                            <span className="text-slate-500">International</span>
                            <p className="text-slate-200">
                              {txn.is_international ? "Yes" : "No"}
                            </p>
                          </div>
                          <div>
                            <span className="text-slate-500">Merchant</span>
                            <p className="text-slate-200">{txn.merchant_id}</p>
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
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-400">
            Showing {page * limit + 1}–
            {Math.min((page + 1) * limit, total)} of {total}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-50"
            >
              Prev
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
