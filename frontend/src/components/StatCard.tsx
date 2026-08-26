import type { ReactNode } from "react";
import { clsx } from "clsx";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export function StatCard({
  label,
  value,
  icon,
  trend,
  suffix,
}: {
  label: string;
  value: string | number;
  icon: ReactNode;
  trend?: number;
  suffix?: string;
}): ReactNode {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
      <div className="flex items-center justify-between">
        <div className="rounded-lg bg-slate-800 p-2.5">{icon}</div>
        {trend !== undefined && (
          <div
            className={clsx(
              "flex items-center gap-1 text-xs font-medium",
              trend > 0 && "text-emerald-400",
              trend < 0 && "text-red-400",
              trend === 0 && "text-slate-400"
            )}
          >
            {trend > 0 ? (
              <TrendingUp className="size-3" />
            ) : trend < 0 ? (
              <TrendingDown className="size-3" />
            ) : (
              <Minus className="size-3" />
            )}
            {Math.abs(trend)}%
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold text-white">
          {value}
          {suffix && (
            <span className="text-sm font-normal text-slate-400 ml-1">
              {suffix}
            </span>
          )}
        </p>
        <p className="mt-1 text-sm text-slate-400">{label}</p>
      </div>
    </div>
  );
}
