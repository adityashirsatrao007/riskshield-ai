import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  BarChart3,
  Shield,
} from "lucide-react";
import { clsx } from "clsx";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/transactions", label: "Transactions", icon: Activity },
  { to: "/alerts", label: "Alerts", icon: AlertTriangle },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
];

export default function Layout() {
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
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto bg-slate-950 p-8">
        <Outlet />
      </main>
    </div>
  );
}
