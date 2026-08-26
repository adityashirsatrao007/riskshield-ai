import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  BarChart3,
  Shield,
  Key,
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
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="w-full max-w-sm rounded-xl border border-slate-800 bg-slate-900 p-8">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg bg-brand-600">
              <Shield className="size-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">RiskShield AI</h1>
              <p className="text-xs text-slate-400">Enter your API key to continue</p>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-xs text-slate-400">API Key</label>
              <div className="relative">
                <Key className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  value={keyInput}
                  onChange={(e) => setKeyInput(e.target.value)}
                  placeholder="X-API-Key"
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 py-2 pl-10 pr-4 text-sm text-slate-200 placeholder-slate-500 focus:border-brand-500 focus:outline-none"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && keyInput.trim()) {
                      localStorage.setItem("riskshield_api_key", keyInput.trim());
                      window.location.reload();
                    }
                  }}
                />
              </div>
            </div>
            <button
              onClick={() => {
                if (keyInput.trim()) {
                  localStorage.setItem("riskshield_api_key", keyInput.trim());
                  window.location.reload();
                }
              }}
              disabled={!keyInput.trim()}
              className="w-full rounded-lg bg-brand-600 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
            >
              Connect
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-64 flex-shrink-0 border-r border-slate-800 bg-slate-900">
        <div className="flex h-16 items-center gap-3 border-b border-slate-800 px-5">
          <div className="flex size-9 items-center justify-center rounded-lg bg-brand-600">
            <Shield className="size-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">RiskShield AI</h1>
            <p className="text-[11px] text-slate-400">Fraud Prevention</p>
          </div>
        </div>
        <nav className="mt-4 space-y-1 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-600/15 text-brand-400"
                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                )
              }
            >
              <item.icon className="size-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute bottom-0 w-64 border-t border-slate-800 p-4">
          <div className="rounded-lg bg-slate-800/50 p-3">
            <p className="text-xs text-slate-400">Razorpay Buildathon</p>
            <p className="text-[11px] text-slate-500">Track 2 — AI Risk Manager</p>
            <button
              onClick={() => {
                localStorage.removeItem("riskshield_api_key");
                window.location.reload();
              }}
              className="mt-2 text-[11px] text-slate-600 hover:text-slate-400"
            >
              Switch API key
            </button>
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto bg-slate-950 p-8">
        <Outlet />
      </main>
    </div>
  );
}
