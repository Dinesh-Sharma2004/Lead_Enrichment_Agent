"use client";

import React from "react";
import { CompanyIntelligence } from "@/lib/types";
import { ConfidenceIndicator } from "./ConfidenceIndicator";
import { EvidenceBadge, ProcessedUrlsList, isValidHttpUrl } from "./EvidenceLinks";
import {
  Building2,
  Users,
  Package,
  Mail,
  Coins,
  Globe2,
  Linkedin,
  FileText,
  Target,
} from "lucide-react";

interface CompanyDetailsProps {
  company: CompanyIntelligence;
}

export function CompanyDetails({ company }: CompanyDetailsProps) {
  return (
    <div className="space-y-6 pt-4 border-t border-slate-800 text-slate-200 text-sm">
      {/* 1. Overview & Audience Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Company Overview */}
        <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Building2 className="w-4 h-4 text-sky-400" />
              Company Overview
            </span>
          </div>
          <p className="text-slate-200 leading-relaxed">
            {company.company_overview || "No company overview found."}
          </p>
          {company.overview_source_url && (
            <div className="pt-2 border-t border-slate-800/80">
              <EvidenceBadge sourceUrl={company.overview_source_url} label="Overview Source" />
            </div>
          )}
        </div>

        {/* Target Audience */}
        <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Target className="w-4 h-4 text-teal-400" />
              Target Audience &amp; ICP
            </span>
          </div>
          <p className="text-slate-200 leading-relaxed">
            {company.target_audience || "Target audience not specified on visited pages."}
          </p>
          {company.target_audience_source_url && (
            <div className="pt-2 border-t border-slate-800/80">
              <EvidenceBadge sourceUrl={company.target_audience_source_url} label="Audience Source" />
            </div>
          )}
        </div>
      </div>

      {/* 2. Products and Services */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Package className="w-4 h-4 text-indigo-400" />
          Products &amp; Services ({company.products_services?.length || 0})
        </h4>

        {company.products_services && company.products_services.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {company.products_services.map((item, idx) => (
              <div
                key={idx}
                className="bg-slate-900/40 p-3.5 rounded-lg border border-slate-800 hover:border-slate-700 transition-colors space-y-2"
              >
                <div className="flex items-start justify-between gap-2">
                  <h5 className="font-semibold text-slate-100 text-sm">{item.name}</h5>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{item.description}</p>
                <div className="pt-2 border-t border-slate-800/60">
                  <EvidenceBadge
                    sourceUrl={item.source_url}
                    grounded={item.grounded}
                    label="Source Reference"
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400 italic">No structured products extracted.</p>
        )}
      </div>

      {/* 3. Leadership & Contacts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Leadership */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Users className="w-4 h-4 text-emerald-400" />
            Leadership &amp; Key People ({company.leadership?.length || 0})
          </h4>

          {company.leadership && company.leadership.length > 0 ? (
            <div className="space-y-2.5">
              {company.leadership.map((leader, idx) => (
                <div
                  key={idx}
                  className="bg-slate-900/40 p-3 rounded-lg border border-slate-800 flex flex-col gap-1.5"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-slate-100">{leader.name}</span>
                      <span className="text-xs text-slate-400 ml-2">({leader.role || "Executive"})</span>
                    </div>

                    {leader.linkedin_url && isValidHttpUrl(leader.linkedin_url) && (
                      <a
                        href={leader.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[11px] text-sky-400 hover:text-sky-300 px-2 py-0.5 rounded bg-sky-950/40 border border-sky-800"
                      >
                        <Linkedin className="w-3 h-3 text-sky-400" />
                        Profile
                      </a>
                    )}
                  </div>
                  <EvidenceBadge
                    sourceUrl={leader.source_url}
                    grounded={leader.grounded}
                    label="Leadership Source"
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No leadership entries identified.</p>
          )}
        </div>

        {/* Contact Information */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Mail className="w-4 h-4 text-rose-400" />
            Public Contact Points ({company.contact_points?.length || 0})
          </h4>

          {company.contact_points && company.contact_points.length > 0 ? (
            <div className="space-y-2.5">
              {company.contact_points.map((contact, idx) => (
                <div
                  key={idx}
                  className="bg-slate-900/40 p-3 rounded-lg border border-slate-800 flex flex-col gap-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 font-medium">{contact.type}:</span>
                    <span className="font-mono text-xs text-slate-100">{contact.value}</span>
                  </div>
                  <EvidenceBadge
                    sourceUrl={contact.source_url}
                    grounded={contact.grounded}
                    label="Contact Source"
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No direct contact addresses harvested.</p>
          )}
        </div>
      </div>

      {/* 4. Confidence & Cost Metrics Breakdown */}
      <div className="bg-slate-900/70 p-4 rounded-lg border border-slate-800 space-y-4">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Coins className="w-4 h-4 text-amber-400" />
          Intelligence Metrics &amp; Provenance
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div>
            <span className="text-slate-400 block mb-1">Dual Confidence Rating:</span>
            <ConfidenceIndicator
              score={company.confidence_score}
              llmScore={company.llm_confidence_score}
              heuristicScore={company.heuristic_confidence_score}
              rationale={company.confidence_rationale}
              showDetails={true}
            />
          </div>

          <div className="space-y-2">
            <div>
              <span className="text-slate-400 block">Extraction Status:</span>
              <span className="font-medium text-slate-200">{company.extraction_status}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Tokens Consumed:</span>
              <span className="font-mono text-slate-200">
                {company.total_tokens_used?.toLocaleString() || 0} tokens
              </span>
            </div>
            <div>
              <span className="text-slate-400 block">Estimated Model Cost:</span>
              <span className="font-mono text-emerald-400">
                ${company.estimated_cost_usd?.toFixed(5) || "0.00000"} USD
              </span>
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-slate-400 block flex items-center gap-1">
              <Globe2 className="w-3.5 h-3.5 text-sky-400" />
              Crawled Pages ({company.all_processed_urls?.length || 0}):
            </span>
            <ProcessedUrlsList urls={company.all_processed_urls || []} />
          </div>
        </div>
      </div>
    </div>
  );
}

