"use client";

import React from "react";
import { ShieldCheck, AlertTriangle, ShieldAlert } from "lucide-react";

interface ConfidenceIndicatorProps {
  score: number;
  llmScore?: number;
  heuristicScore?: number;
  rationale?: string;
  showDetails?: boolean;
}

export function ConfidenceIndicator({
  score,
  llmScore,
  heuristicScore,
  rationale,
  showDetails = false,
}: ConfidenceIndicatorProps) {
  const percent = Math.round(score * 100);

  let badgeColor = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
  let barColor = "bg-emerald-500";
  let Icon = ShieldCheck;

  if (score < 0.5) {
    badgeColor = "bg-rose-500/10 text-rose-400 border-rose-500/20";
    barColor = "bg-rose-500";
    Icon = ShieldAlert;
  } else if (score < 0.8) {
    badgeColor = "bg-amber-500/10 text-amber-400 border-amber-500/20";
    barColor = "bg-amber-500";
    Icon = AlertTriangle;
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-2">
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${badgeColor}`}
          title="Dual-engine minimum confidence (LLM vs Rule-based Heuristics)"
        >
          <Icon className="w-3.5 h-3.5" />
          {percent}% Confidence
        </span>
      </div>

      {showDetails && (
        <div className="text-xs text-slate-400 space-y-1.5 mt-1 bg-slate-900/50 p-2.5 rounded-md border border-slate-800">
          <div className="flex justify-between items-center text-[11px]">
            <span>Dual Confidence Bar:</span>
            <span className="font-mono text-slate-300">{percent}%</span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div
              className={`h-full ${barColor} transition-all duration-300`}
              style={{ width: `${percent}%` }}
            />
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-800/80 text-[11px]">
            <div>
              <span className="text-slate-400">LLM Rating: </span>
              <span className="font-medium text-slate-300">
                {llmScore !== undefined ? `${Math.round(llmScore * 100)}%` : "N/A"}
              </span>
            </div>
            <div>
              <span className="text-slate-400">Heuristic: </span>
              <span className="font-medium text-slate-300">
                {heuristicScore !== undefined ? `${Math.round(heuristicScore * 100)}%` : "N/A"}
              </span>
            </div>
          </div>

          {rationale && (
            <p className="text-[11px] text-slate-300 pt-1 italic border-t border-slate-800/60">
              &ldquo;{rationale}&rdquo;
            </p>
          )}
        </div>
      )}
    </div>
  );
}

