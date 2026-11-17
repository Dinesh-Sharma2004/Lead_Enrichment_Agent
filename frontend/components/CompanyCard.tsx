"use client";

import React, { useState } from "react";
import { CompanyIntelligence } from "@/lib/types";
import { CompanyDetails } from "./CompanyDetails";
import { ConfidenceIndicator } from "./ConfidenceIndicator";
import {
  ChevronDown,
  ChevronUp,
  Building2,
  Users,
  Package,
  CheckCircle,
  AlertTriangle,
  XCircle,
} from "lucide-react";

interface CompanyCardProps {
  company: CompanyIntelligence;
  defaultExpanded?: boolean;
}

export function CompanyCard({ company, defaultExpanded = false }: CompanyCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const isFailed =
    company.extraction_status.toLowerCase().includes("failed") ||
    company.confidence_score === 0;

  const isPartial =
    company.extraction_status.toLowerCase().includes("partial") ||
    (company.confidence_score > 0 && company.confidence_score < 0.8);

  return (
    <div
      className={`rounded-xl border transition-all duration-200 overflow-hidden ${
        isFailed
          ? "border-rose-900/40 bg-slate-900/60"
          : isPartial
          ? "border-amber-900/40 bg-slate-900/80"
          : "border-slate-800 bg-slate-900 hover:border-slate-700"
      }`}
    >
      {/* Header bar / Toggle */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer select-none hover:bg-slate-800/40 transition-colors"
      >
        <div className="flex items-start sm:items-center gap-3">
          <div className="p-2.5 rounded-lg bg-slate-800 text-sky-400 border border-slate-700/80 flex-shrink-0">
            <Building2 className="w-5 h-5" />
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-slate-100 text-base">
                {company.company_name || company.domain}
              </h3>
              <span className="text-xs text-slate-400 font-mono">({company.domain})</span>
            </div>

            <p className="text-xs text-slate-400 line-clamp-1 mt-0.5 max-w-xl">
              {company.company_overview || "No overview recorded."}
            </p>
          </div>
        </div>

        {/* Right side status / metrics */}
        <div className="flex items-center gap-3 self-end sm:self-center flex-shrink-0">
          <div className="flex items-center gap-2 text-xs">
            <span
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700"
              title="Products identified"
            >
              <Package className="w-3 h-3 text-indigo-400" />
              {company.products_services?.length || 0}
            </span>

            <span
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700"
              title="Leadership profiles"
            >
              <Users className="w-3 h-3 text-emerald-400" />
              {company.leadership?.length || 0}
            </span>
          </div>

          <ConfidenceIndicator score={company.confidence_score} />

          <button
            type="button"
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            aria-label={isExpanded ? "Collapse details" : "Expand details"}
          >
            {isExpanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* Expanded Details Body */}
      {isExpanded && (
        <div className="px-5 pb-5 pt-1">
          <CompanyDetails company={company} />
        </div>
      )}
    </div>
  );
}

