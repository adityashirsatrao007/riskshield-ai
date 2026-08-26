import { clsx } from "clsx";
import type { ReactNode } from "react";

const levelStyles: Record<string, string> = {
  low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
};

export function RiskBadge({
  level,
  score,
}: {
  level: string;
  score?: number;
}): ReactNode {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        levelStyles[level] || levelStyles.low
      )}
    >
      <span className="size-1.5 rounded-full bg-current" />
      {level.charAt(0).toUpperCase() + level.slice(1)}
      {score !== undefined && (
        <span className="opacity-60 ml-0.5">{(score * 100).toFixed(1)}%</span>
      )}
    </span>
  );
}
