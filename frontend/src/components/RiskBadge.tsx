import { clsx } from "clsx";
import type { ReactNode } from "react";

const levelConfig = {
  low: {
    gradient: "from-emerald-500 to-teal-500",
    glow: "shadow-emerald-500/20",
    dot: "bg-emerald-400 shadow-lg shadow-emerald-400/50",
    bg: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
  },
  medium: {
    gradient: "from-amber-500 to-orange-500",
    glow: "shadow-amber-500/20",
    dot: "bg-amber-400 shadow-lg shadow-amber-400/50",
    bg: "bg-amber-500/10 border-amber-500/20 text-amber-400",
  },
  high: {
    gradient: "from-orange-500 to-red-500",
    glow: "shadow-orange-500/20",
    dot: "bg-orange-400 shadow-lg shadow-orange-400/50",
    bg: "bg-orange-500/10 border-orange-500/20 text-orange-400",
  },
  critical: {
    gradient: "from-red-500 to-rose-600",
    glow: "shadow-red-500/20",
    dot: "bg-red-400 shadow-lg shadow-red-400/50 animate-pulse-slow",
    bg: "bg-red-500/10 border-red-500/20 text-red-400",
  },
};

export function RiskBadge({
  level,
  score,
}: {
  level: string;
  score?: number;
}): ReactNode {
  const config = level in levelConfig ? levelConfig[level as keyof typeof levelConfig] : levelConfig.low;

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold backdrop-blur-sm",
        config.bg
      )}
    >
      <span className={clsx("size-1.5 rounded-full", config.dot)} />
      {level.charAt(0).toUpperCase() + level.slice(1)}
      {score !== undefined && (
        <span className="opacity-60 ml-0.5">
          {(score * 100).toFixed(1)}%
        </span>
      )}
    </span>
  );
}
