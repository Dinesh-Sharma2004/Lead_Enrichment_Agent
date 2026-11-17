"use client";

import React from "react";
import { DomainStatusItem } from "@/lib/types";
import {
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  StopCircle,
  Clock,
} from "lucide-react";

interface ProcessingStatusProps {
  items: DomainStatusItem[];
  onCancel: () => void;
  isLoading: boolean;
}

export function ProcessingStatus({ items, onCancel, isLoading }: ProcessingStatusProps) {
  if (items.length === 0) return null;

  const completedCount = items.filter(
    (i) => i.stage === "Completed" || i.stage === "Partial extraction" || i.stage === "Failed"
  ).length;

  const total = items.length;
  const progressPercent = Math.round((completedCount / total) * 100);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
      {/* Header with Title and Cancel button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          {isLoading ? (
            <Loader2 className="w-4 h-4 text-sky-400 animate-spin" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          )}
          <span className="font-semibold text-slate-100 text-sm">
            {isLoading ? "Enrichment in Progress" : "Batch Processing Complete"}
          </span>
          <span className="text-xs font-mono text-slate-400">
            ({completedCount}/{total} processed)
          </span>
        </div>

        {isLoading && (
          <button
            type="button"
            onClick={onCancel}
            className="text-xs px-3 py-1 rounded-md bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-colors flex items-center gap-1.5 font-medium"
          >
            <StopCircle className="w-3.5 h-3.5" />
            Cancel Job
          </button>
        )}
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
        <div
          className={`h-full transition-all duration-300 ${
            isLoading ? "bg-sky-500" : "bg-emerald-500"
          }`}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Individual Domain Status Rows */}
      <div className="space-y-2 pt-1">
        {items.map((item, idx) => {
          let stageBadge = (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400">
              <Clock className="w-3 h-3 text-slate-500" />
              Queued
            </span>
          );

          if (item.stage === "Discovering pages" || item.stage === "Extracting information" || item.stage === "Enriching leadership") {
            stageBadge = (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-sky-400">
                <Loader2 className="w-3 h-3 animate-spin" />
                {item.stage}
              </span>
            );
          } else if (item.stage === "Completed") {
            stageBadge = (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                <CheckCircle2 className="w-3 h-3" />
                Completed
              </span>
            );
          } else if (item.stage === "Partial extraction") {
            stageBadge = (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-400">
                <AlertTriangle className="w-3 h-3" />
                Partial Extraction
              </span>
            );
          } else if (item.stage === "Failed") {
            stageBadge = (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-400">
                <XCircle className="w-3 h-3" />
                Failed
              </span>
            );
          }

          return (
            <div
              key={idx}
              className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs"
            >
              <div className="flex items-center gap-2">
                <span className="font-mono font-medium text-slate-200">{item.domain}</span>
                {item.error && (
                  <span className="text-[11px] text-rose-400 truncate max-w-xs sm:max-w-md">
                    ({item.error})
                  </span>
                )}
              </div>

              <div>{stageBadge}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

