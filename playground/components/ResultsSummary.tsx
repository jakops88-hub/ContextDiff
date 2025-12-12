"use client";

import React from "react";
import { DiffSummary } from "@/lib/api";
import { AlertTriangle, CheckCircle2, XCircle, AlertCircle, Clock, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface ResultsSummaryProps {
  summary: DiffSummary;
  changesCount: number;
  analysisTime?: number;
  criticalCount?: number;
  warningCount?: number;
}

export default function ResultsSummary({
  summary,
  changesCount,
  analysisTime,
  criticalCount = 0,
  warningCount = 0,
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
    <div className="w-full space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Enterprise Header */}
      <div className="bg-gradient-to-br from-white to-zinc-50 border-2 border-zinc-200 rounded-xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-zinc-900 mb-1">Analysis Complete</h2>
            <p className="text-sm text-zinc-600">
              AI-powered semantic difference detection • Powered by GPT-4o-mini
            </p>
          </div>
          {analysisTime && (
            <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg">
              <Clock className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-semibold text-blue-700">{analysisTime.toFixed(1)}s</span>
            </div>
          )}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          {/* Safety Status */}
          <div className={cn(
            "border-2 rounded-lg p-4 flex flex-col items-center justify-center",
            is_safe ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"
          )}>
            {is_safe ? (
              <CheckCircle2 className="w-7 h-7 text-green-600 mb-2" />
            ) : (
              <XCircle className="w-7 h-7 text-red-600 mb-2" />
            )}
            <div className={cn(
              "text-xl font-bold mb-1",
              is_safe ? "text-green-700" : "text-red-700"
            )}>
              {is_safe ? "SAFE" : "REVIEW"}
            </div>
            <div className="text-xs text-zinc-600 font-medium">Status</div>
          </div>

          {/* Risk Score */}
          <div className={cn("border-2 rounded-lg p-4 flex flex-col items-center justify-center", getRiskBgColor())}>
            <TrendingUp className={cn("w-7 h-7 mb-2", getRiskColor())} />
            <div className={cn("text-2xl font-bold mb-1", getRiskColor())}>
              {risk_score}
            </div>
            <div className="text-xs text-zinc-600 font-medium">Risk Score</div>
          </div>

          {/* Changes */}
          <div className="border-2 border-blue-200 bg-blue-50 rounded-lg p-4 flex flex-col items-center justify-center">
            <div className="text-2xl font-bold text-blue-700 mb-1">{changesCount}</div>
            <div className="text-xs text-blue-600 font-medium uppercase">Changes</div>
          </div>

          {/* Change Level */}
          <div className="border-2 border-indigo-200 bg-indigo-50 rounded-lg p-4 flex flex-col items-center justify-center">
            <div className="text-sm font-bold text-indigo-700 mb-1 text-center">
              {semantic_change_level}
            </div>
            <div className="text-xs text-indigo-600 font-medium">Level</div>
          </div>
        </div>

        {/* Severity Breakdown */}
        <div className="grid grid-cols-3 gap-3 pt-4 border-t border-zinc-200">
          <div className="flex items-center justify-between px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
            <span className="text-xs font-medium text-red-700">Critical</span>
            <span className="text-sm font-bold text-red-900">{criticalCount}</span>
          </div>
          <div className="flex items-center justify-between px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg">
            <span className="text-xs font-medium text-yellow-700">Warning</span>
            <span className="text-sm font-bold text-yellow-900">{warningCount}</span>
          </div>
          <div className="flex items-center justify-between px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
            <span className="text-xs font-medium text-blue-700">Info</span>
            <span className="text-sm font-bold text-blue-900">{changesCount - criticalCount - warningCount}</span>
          </div>
        </div>

        {/* Enterprise Warning */}
        {!is_safe && (
          <div className="mt-4 bg-red-50 border-2 border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-red-900 mb-1">
                  ⚠️ Review Required Before Publication
                </h4>
                <p className="text-xs text-red-800 leading-relaxed">
                  This content contains {criticalCount} critical {criticalCount === 1 ? 'issue' : 'issues'} that may impact 
                  accuracy, compliance, or brand reputation. Click highlighted sections for detailed AI analysis.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {is_safe && criticalCount === 0 && (
          <div className="mt-4 bg-green-50 border-2 border-green-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-green-900 mb-1">
                  ✓ Content Approved
                </h4>
                <p className="text-xs text-green-800 leading-relaxed">
                  No critical issues detected. This content is safe for publication, though you may want to review 
                  {warningCount > 0 && ` ${warningCount} minor suggestion${warningCount === 1 ? '' : 's'}`}.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Guide */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-3 shadow-sm">
        <p className="text-xs text-zinc-700 text-center font-medium">
          <span className="text-blue-700 font-bold">💡 Click</span> highlighted text to inspect • 
          <span className="text-green-700 font-bold">Export</span> as JSON/MD • 
          <span className="text-purple-700 font-bold">ESC</span> to close
        </p>
      </div>
    </div>
  );
}
