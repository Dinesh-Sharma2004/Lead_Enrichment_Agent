"use client";

import React from "react";
import { ExternalLink, CheckCircle2, AlertCircle } from "lucide-react";

interface EvidenceBadgeProps {
  sourceUrl?: string | null;
  grounded?: boolean;
  label?: string;
}

export function isValidHttpUrl(stringToTest?: string | null): boolean {
  if (!stringToTest) return false;
  try {
    const url = new URL(stringToTest);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export function EvidenceBadge({ sourceUrl, grounded = true, label }: EvidenceBadgeProps) {
  const isUrl = isValidHttpUrl(sourceUrl);

  return (
    <div className="inline-flex items-center gap-1.5 flex-wrap text-xs">
      {grounded ? (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3 h-3" />
          Verified Grounded
        </span>
      ) : (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <AlertCircle className="w-3 h-3" />
          Ungrounded / Search Fallback
        </span>
      )}

      {sourceUrl && isUrl ? (
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sky-400 hover:text-sky-300 underline underline-offset-2 transition-colors max-w-[240px] truncate"
          title={sourceUrl}
        >
          <span>{label || new URL(sourceUrl).pathname || sourceUrl}</span>
          <ExternalLink className="w-2.5 h-2.5 flex-shrink-0" />
        </a>
      ) : sourceUrl ? (
        <span className="text-slate-400 font-mono text-[11px]">{sourceUrl}</span>
      ) : null}
    </div>
  );
}

export function ProcessedUrlsList({ urls }: { urls: string[] }) {
  if (!urls || urls.length === 0) {
    return <span className="text-xs text-slate-400">No pages crawled</span>;
  }

  return (
    <div className="flex flex-wrap gap-1.5 mt-1">
      {urls.map((url, idx) => {
        const isUrl = isValidHttpUrl(url);
        return isUrl ? (
          <a
            key={idx}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-slate-800 text-sky-400 hover:text-sky-300 border border-slate-700 transition-colors"
          >
            <span className="truncate max-w-[200px]">{url}</span>
            <ExternalLink className="w-2.5 h-2.5 flex-shrink-0" />
          </a>
        ) : (
          <span
            key={idx}
            className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700"
          >
            {url}
          </span>
        );
      })}
    </div>
  );
}

