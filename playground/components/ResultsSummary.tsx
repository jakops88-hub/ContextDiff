"use client";

import React from "react";
import { DiffSummary } from "@/lib/api";
import { AlertTriangle, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ResultsSummaryProps {
  summary: DiffSummary;
  changesCount: number;
}

export default function ResultsSummary({
  summary,
  changesCount,
}: ResultsSummaryProps) {
  const { is_safe, risk_score, semantic_change_level } = summary;

  const getRiskColor = () => {
    if (risk_score >= 70) return "text-red-700";
    if (risk_score >= 40) return "text-yellow-700";
    return "text-green-700";
  };

  const getRiskBgColor = () => {
    if (risk_score >= 70) return "bg-red-100 border-red-300";
    if (risk_score >= 40) return "bg-yellow-100 border-yellow-300";
    return "bg-green-100 border-green-300";
  };

  const getRiskIcon = () => {
    if (risk_score >= 70)
      return <XCircle className="w-6 h-6 text-red-600" />;
    if (risk_score >= 40)
      return <AlertTriangle className="w-6 h-6 text-yellow-600" />;
    return <CheckCircle2 className="w-6 h-6 text-green-600" />;
  };

  const getRiskLabel = () => {
    if (risk_score >= 70) return "High Risk";
    if (risk_score >= 40) return "Moderate Risk";
    return "Safe";
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Main Risk Score Card */}
      <div
        className={cn(
          "border-2 rounded-xl p-6 shadow-lg transition-all",
          getRiskBgColor()
        )}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {getRiskIcon()}
            <div>
              <h3 className={cn("text-2xl font-bold", getRiskColor())}>
                {getRiskLabel()}
              </h3>
              <p className="text-sm text-zinc-700 mt-1">
                Risk Score: <span className="font-bold">{risk_score}</span>/100
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-zinc-600 uppercase tracking-wide mb-1">
              Semantic Change Level
            </p>
            <span
              className={cn(
                "inline-block px-3 py-1 text-sm font-semibold rounded-lg",
                semantic_change_level === "CRITICAL" && "bg-red-600 text-white",
                semantic_change_level === "MAJOR" && "bg-orange-600 text-white",
                semantic_change_level === "MODERATE" && "bg-yellow-600 text-white",
                semantic_change_level === "MINOR" && "bg-blue-600 text-white",
                semantic_change_level === "NONE" && "bg-green-600 text-white"
              )}
            >
              {semantic_change_level}
            </span>
          </div>
        </div>

        {!is_safe && (
          <div className="mt-4 flex items-start gap-2 bg-white/50 rounded-lg p-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-zinc-800">
              <strong>Warning:</strong> The AI-generated text contains significant
              semantic differences. Review the highlighted changes carefully before
              using this content.
            </p>
          </div>
        )}
      </div>

      {/* Changes Count */}
      <div className="bg-white border border-zinc-200 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <p className="text-sm text-zinc-700">
            <span className="font-bold text-lg text-zinc-900">{changesCount}</span>{" "}
            semantic {changesCount === 1 ? "change" : "changes"} detected
          </p>
          <p className="text-xs text-zinc-500">
            Hover over highlighted text below to see details
          </p>
        </div>
      </div>
    </div>
  );
}
