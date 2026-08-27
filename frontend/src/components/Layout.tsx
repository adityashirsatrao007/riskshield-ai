import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  BarChart3,
  Shield,
  Key,
  Zap,
} from "lucide-react";
import { clsx } from "clsx";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/transactions", label: "Transactions", icon: Activity },
  { to: "/alerts", label: "Alerts", icon: AlertTriangle },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
];

export default function Layout() {
  const [keyInput, setKeyInput] = useState("");
  const storedKey = localStorage.getItem("riskshield_api_key");

  if (!storedKey) {
    return (
      <div className="noise-bg flex min-h-screen items-center justify-center bg-[#030712]">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -left-40 -top-40 h-80 w-80 rounded-full bg-indigo-500/10 blur-[120px]" />
          <div className="absolute -bottom-40 -right-40 h-80 w-80 rounded-full bg-purple-500/10 blur-[120px]" />
        </div>
        <div className="animate-scale-in glass-card relative w-full max-w-sm rounded-2xl p-8">
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500/5 via-transparent to-purple-500/5" />
          <div className="relative">
            <div className="mb-6 flex items-center gap-3">
              <div className="relative flex size-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600">
                <Shield className="size-6 text-white" />
                <div className="absolute -right-1 -top-1 flex size-5 items-center justify-center rounded-full bg-emerald-500">
                  <Zap className="size-3 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">RiskShield AI</h1>
                <p className="text-xs text-slate-400">
                  Enter your API key to continue
                </p>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-slate-400">
                  API Key
                </label>
                <div className="relative">
                  <Key className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-500" />
                  <input
                    type="password"
                    value={keyInput}
                    onChange={(e) => setKeyInput(e.target.value)}
                    placeholder="X-API-Key"
                    className="w-full rounded-xl border border-slate-700/50 bg-slate-800/50 py-2.5 pl-10 pr-4 text-sm text-slate-200 placeholder-slate-500 backdrop-blur-sm focus:border-indigo-500/50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && keyInput.trim()) {
                        localStorage.setItem(
                          "riskshield_api_key",
                          keyInput.trim()
                        );
                        window.location.reload();
                      }
                    }}
                  />
                </div>
              </div>
              <button
                onClick={() => {
                  if (keyInput.trim()) {
                    localStorage.setItem(
                      "riskshield_api_key",
                      keyInput.trim()
                    );
                    window.location.reload();
                  }
                }}
                disabled={!keyInput.trim()}
                className="w-full rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:shadow-indigo-500/40 hover:brightness-110 disabled:opacity-50 disabled:shadow-none"
              >
                Connect
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="noise-bg flex h-screen overflow-hidden bg-[#030712]">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -left-40 top-1/4 h-96 w-96 rounded-full bg-indigo-500/5 blur-[150px]" />
        <div className="absolute -right-40 top-3/4 h-96 w-96 rounded-full bg-purple-500/5 blur-[150px]" />
      </div>

      <aside className="glass-strong relative z-10 flex w-64 flex-shrink-0 flex-col border-r border-slate-800/50">
        <div className="flex h-16 items-center gap-3 border-b border-slate-800/50 px-5">
          <div className="relative flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20">
            <Shield className="size-5 text-white" />
            <div className="absolute -right-0.5 -top-0.5 flex size-3.5 items-center justify-center rounded-full border-2 border-slate-900 bg-emerald-500">
              <div className="size-1.5 rounded-full bg-white animate-pulse-slow" />
            </div>
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">RiskShield AI</h1>
            <p className="text-[11px] text-slate-500">Fraud Prevention</p>
          </div>
        </div>

        <nav className="mt-4 flex-1 space-y-1 px-3">
          {navItems.map((item, i) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              style={{ animationDelay: `${i * 80}ms` }}
              className={({ isActive }) =>
                clsx(
                  "animate-slide-right group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                  isActive
                    ? "bg-gradient-to-r from-indigo-500/15 to-purple-500/10 text-indigo-400 shadow-lg shadow-indigo-500/5"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                )
              }
            >
              {({ isActive }) => (
                <>
                  <div
                    className={clsx(
                      "flex size-8 items-center justify-center rounded-lg transition-all",
                      isActive
                        ? "bg-indigo-500/20 text-indigo-400"
                        : "bg-slate-800/50 text-slate-500 group-hover:bg-slate-700/50 group-hover:text-slate-300"
                    )}
                  >
                    <item.icon className="size-4" />
                  </div>
                  {item.label}
                  {isActive && (
                    <div className="ml-auto size-1.5 rounded-full bg-indigo-400 shadow-lg shadow-indigo-400/50" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-slate-800/50 p-4">
          <div className="glass-card rounded-xl p-3">
            <p className="text-xs font-medium text-slate-300">
              Razorpay Buildathon
            </p>
            <p className="text-[11px] text-slate-500">
              Track 2 — AI Risk Manager
            </p>
            <button
              onClick={() => {
                localStorage.removeItem("riskshield_api_key");
                window.location.reload();
              }}
              className="mt-2 text-[11px] text-slate-600 transition-colors hover:text-slate-400"
            >
              Switch API key
            </button>
          </div>
        </div>
      </aside>

      <main className="relative z-10 flex-1 overflow-y-auto p-8">
        <Outlet />
      </main>
    </div>
  );
}
