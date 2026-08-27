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
    const duration = 800;
    const steps = 30;
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
          ? Math.round(current).toLocaleString()
          : num % 1 !== 0
          ? current.toFixed(1)
          : String(Math.round(current))
      );
    }, duration / steps);
    return () => clearInterval(timer);
  }, [num]);

  return (
    <span>
      {prefix}
      {display}
      {suffix && (
        <span className="ml-1 text-sm font-normal text-slate-400">{suffix}</span>
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

  return (
    <div
      className={clsx(
        "gradient-border group rounded-2xl p-5 transition-all duration-300 hover:scale-[1.02]",
        glowMap[color]
      )}
    >
      <div className="flex items-center justify-between">
        <div
          className={clsx(
            "flex size-10 items-center justify-center rounded-xl bg-gradient-to-br shadow-lg",
            gradientMap[color]
          )}
        >
          {icon}
        </div>
        {trend !== undefined && (
          <div
            className={clsx(
              "flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
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
      <div className="mt-4">
        <p className="text-2xl font-bold text-white">
          <AnimatedNumber value={value} suffix={suffix} />
        </p>
        <p className="mt-1 text-sm text-slate-400">{label}</p>
      </div>
    </div>
  );
}
