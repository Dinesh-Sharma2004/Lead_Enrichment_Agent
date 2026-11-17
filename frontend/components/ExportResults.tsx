"use client";

import React from "react";
import { CompanyIntelligence } from "@/lib/types";
import { generateCompanyCsv, triggerFileDownload } from "@/lib/csv";
import { Download, FileJson, FileSpreadsheet } from "lucide-react";

interface ExportResultsProps {
  companies: CompanyIntelligence[];
}

export function ExportResults({ companies }: ExportResultsProps) {
  if (companies.length === 0) return null;

  const handleDownloadJson = () => {
    const jsonStr = JSON.stringify(companies, null, 2);
    triggerFileDownload(jsonStr, "lead_enrichment_results.json", "application/json");
  };

  const handleDownloadCsv = () => {
    const csvStr = generateCompanyCsv(companies);
    triggerFileDownload(csvStr, "lead_enrichment_results.csv", "text/csv;charset=utf-8;");
  };

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={handleDownloadJson}
        className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors flex items-center gap-2 shadow-sm"
      >
        <FileJson className="w-3.5 h-3.5 text-sky-400" />
        Download JSON
      </button>

      <button
        type="button"
        onClick={handleDownloadCsv}
        className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors flex items-center gap-2 shadow-sm"
      >
        <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
        Download CSV
      </button>
    </div>
  );
}

