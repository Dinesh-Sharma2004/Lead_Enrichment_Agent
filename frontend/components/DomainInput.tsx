"use client";

import React, { useState } from "react";
import { Sparkles, Trash2, AlertCircle, Play, Bookmark } from "lucide-react";

interface DomainInputProps {
  onEnrich: (domains: string[]) => void;
  isLoading: boolean;
  maxDomains?: number;
}

const SAMPLE_DOMAINS = ["stripe.com", "supabase.com", "postman.com"];

export function DomainInput({ onEnrich, isLoading, maxDomains = 3 }: DomainInputProps) {
  const [text, setText] = useState<string>("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const parseDomains = (raw: string): string[] => {
    return raw
      .split(/[\n,]+/)
      .map((d) =>
        d
          .trim()
          .toLowerCase()
          .replace(/^https?:\/\//, "")
          .split("/")[0]
          .split("?")[0]
      )
      .filter((d) => Boolean(d) && d.includes("."));
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    setValidationError(null);
  };

  const handleLoadSamples = () => {
    setText(SAMPLE_DOMAINS.join("\n"));
    setValidationError(null);
  };

  const handleClear = () => {
    setText("");
    setValidationError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    const domains = parseDomains(text);

    if (domains.length === 0) {
      setValidationError("Please enter at least one valid domain (e.g. stripe.com).");
      return;
    }

    if (domains.length > maxDomains) {
      setValidationError(
        `Maximum ${maxDomains} domains allowed per batch to prevent serverless timeout. You submitted ${domains.length}.`
      );
      return;
    }

    // SSRF / Localhost check
    const invalid = domains.find(
      (d) =>
        d === "localhost" ||
        d.startsWith("127.") ||
        d.startsWith("192.168.") ||
        d.startsWith("10.") ||
        d.includes("metadata.google.internal")
    );
    if (invalid) {
      setValidationError(`Domain '${invalid}' is a private or restricted destination.`);
      return;
    }

    onEnrich(domains);
  };

  const domainCount = parseDomains(text).length;

  return (
    <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <div>
          <label htmlFor="domains-textarea" className="font-semibold text-slate-100 text-sm flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-400" />
            Target Company Domains
          </label>
          <p className="text-xs text-slate-400 mt-0.5">
            Enter up to {maxDomains} company website domains (one per line).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleLoadSamples}
            disabled={isLoading}
            className="text-xs px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors flex items-center gap-1.5"
          >
            <Bookmark className="w-3 h-3 text-sky-400" />
            Load Samples
          </button>

          {text && (
            <button
              type="button"
              onClick={handleClear}
              disabled={isLoading}
              className="text-xs px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 border border-slate-700 hover:border-rose-800 transition-colors flex items-center gap-1"
            >
              <Trash2 className="w-3 h-3" />
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="relative">
        <textarea
          id="domains-textarea"
          value={text}
          onChange={handleTextChange}
          placeholder="e.g.&#10;stripe.com&#10;notion.so&#10;linear.app"
          rows={4}
          disabled={isLoading}
          className="w-full bg-slate-950/90 text-slate-100 font-mono text-sm rounded-lg border border-slate-800 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 p-3.5 outline-none resize-y placeholder:text-slate-400"
        />

        <div className="absolute right-3 bottom-3 text-[11px] font-mono text-slate-400 pointer-events-none">
          {domainCount} / {maxDomains} domains
        </div>
      </div>

      {validationError && (
        <div className="mt-2.5 p-2.5 rounded-md bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      <div className="mt-4 flex items-center justify-between gap-4">
        <p className="text-xs text-slate-400 hidden sm:block">
          Autonomous link crawling, BeautifulSoup cleaning &amp; Groq AI synthesis.
        </p>

        <button
          type="submit"
          disabled={isLoading || domainCount === 0}
          className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-sm transition-all shadow-md shadow-sky-500/10 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              Enriching Pipeline...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              Enrich Companies
            </>
          )}
        </button>
      </div>
    </form>
  );
}

