import { type ReactNode, useEffect, useState } from "react";
import { clsx } from "clsx";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

function AnimatedNumber({ value, suffix }: { value: string | number; suffix?: string }) {
  const [display, setDisplay] = useState("0");
  const num = typeof value === "string" ? parseFloat(value.replace(/[^0-9.]/g, "")) : value;
  const prefix = typeof value === "string" ? value.replace(/[0-9.,]+.*/, "") : "";

  useEffect(() => {
    if (isNaN(num)) {
      setDisplay(String(value));
      return;
    }
    const duration = 900;
    const steps = 40;
    const increment = num / steps;
    let current = 0;
    let step = 0;
    const timer = setInterval(() => {
      step++;
      current += increment;
      if (step >= steps) {
        current = num;
        clearInterval(timer);
      }
      setDisplay(
        num >= 1000
          ? Math.round(current).toLocaleString("en-IN")
          : num % 1 !== 0
          ? current.toFixed(1)
          : String(Math.round(current))
      );
    }, duration / steps);
    return () => clearInterval(timer);
  }, [num]);

  return (
    <span className="tabular-nums">
      {prefix}
      {display}
      {suffix && (
        <span className="ml-1.5 text-sm font-medium text-slate-400/80">{suffix}</span>
      )}
    </span>
  );
}

export function StatCard({
  label,
  value,
  icon,
  trend,
  suffix,
  color = "indigo",
}: {
  label: string;
  value: string | number;
  icon: ReactNode;
  trend?: number;
  suffix?: string;
  color?: "indigo" | "emerald" | "amber" | "red" | "purple";
}): ReactNode {
  const glowMap = {
    indigo: "glow-blue",
    emerald: "glow-emerald",
    amber: "glow-amber",
    red: "glow-red",
    purple: "glow-purple",
  };

  const gradientMap = {
    indigo: "from-indigo-500 to-blue-500",
    emerald: "from-emerald-500 to-teal-500",
    amber: "from-amber-500 to-orange-500",
    red: "from-red-500 to-rose-500",
    purple: "from-purple-500 to-pink-500",
  };

  const bgGlow = {
    indigo: "bg-indigo-500/[0.03]",
    emerald: "bg-emerald-500/[0.03]",
    amber: "bg-amber-500/[0.03]",
    red: "bg-red-500/[0.03]",
    purple: "bg-purple-500/[0.03]",
  };

  return (
    <div
      className={clsx(
        "gradient-border group relative overflow-hidden rounded-2xl p-6",
        glowMap[color]
      )}
    >
      <div className={clsx("absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100", bgGlow[color])} />

      <div className="relative flex items-start justify-between">
        <div
          className={clsx(
            "flex size-11 items-center justify-center rounded-xl bg-gradient-to-br shadow-lg shadow-black/20",
            gradientMap[color]
          )}
        >
          {icon}
        </div>
        {trend !== undefined && (
          <div
            className={clsx(
              "flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide",
              trend > 0 && "bg-emerald-500/10 text-emerald-400",
              trend < 0 && "bg-red-500/10 text-red-400",
              trend === 0 && "bg-slate-500/10 text-slate-400"
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

      <div className="relative mt-5">
        <p className="text-[28px] font-bold tracking-tight text-white leading-none">
          <AnimatedNumber value={value} suffix={suffix} />
        </p>
        <p className="mt-2 text-[13px] font-medium text-slate-400/80 tracking-wide uppercase">{label}</p>
      </div>
    </div>
  );
}
