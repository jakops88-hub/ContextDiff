"use client";

import React from "react";
import { SemanticChange } from "@/lib/api";
import { cn } from "@/lib/utils";
import { X, AlertTriangle, Info, AlertCircle } from "lucide-react";

interface ChangeDetailCardProps {
  change: SemanticChange | null;
  onClose: () => void;
}

function getTypeColor(type: string): string {
  switch (type) {
    case "FACTUAL":
      return "bg-red-50 text-red-700 border-red-200";
    case "TONE":
      return "bg-yellow-50 text-yellow-700 border-yellow-200";
    case "OMISSION":
      return "bg-orange-50 text-orange-700 border-orange-200";
    case "ADDITION":
      return "bg-blue-50 text-blue-700 border-blue-200";
    case "FORMATTING":
      return "bg-purple-50 text-purple-700 border-purple-200";
    default:
      return "bg-zinc-50 text-zinc-700 border-zinc-200";
  }
}

function getSeverityIcon(severity: string) {
  switch (severity) {
    case "critical":
      return <AlertCircle className="w-4 h-4" />;
    case "warning":
      return <AlertTriangle className="w-4 h-4" />;
    default:
      return <Info className="w-4 h-4" />;
  }
}

function getSeverityColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "bg-red-100 text-red-800 border-red-300";
    case "warning":
      return "bg-yellow-100 text-yellow-800 border-yellow-300";
    default:
      return "bg-blue-100 text-blue-800 border-blue-300";
  }
}

export default function ChangeDetailCard({ change, onClose }: ChangeDetailCardProps) {
  const [copyStatus, setCopyStatus] = React.useState<'idle' | 'json' | 'md'>('idle');
  
  if (!change) return null;

  // Handle Escape key to close
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Reset copy status after 2 seconds
  React.useEffect(() => {
    if (copyStatus !== 'idle') {
      const timer = setTimeout(() => setCopyStatus('idle'), 2000);
      return () => clearTimeout(timer);
    }
  }, [copyStatus]);

  const handleCopyJSON = async () => {
    await navigator.clipboard.writeText(JSON.stringify(change, null, 2));
    setCopyStatus('json');
  };

  const handleExportMD = async () => {
    const md = `## ${change.type} Change (${change.severity})\n\n**Description:** ${change.description}\n\n**AI Reasoning:** ${change.reasoning}\n\n**Original:** ${change.original_span.text}\n\n**Generated:** ${change.generated_span.text}`;
    await navigator.clipboard.writeText(md);
    setCopyStatus('md');
  };

  return (
    <div className="bg-white border-2 border-zinc-300 rounded-xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom duration-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-zinc-50 to-white border-b border-zinc-200 px-6 py-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3 flex-1">
            {/* Type Badge */}
            <span
              className={cn(
                "px-3 py-1.5 text-sm font-bold rounded-lg border-2 uppercase tracking-wide",
                getTypeColor(change.type)
              )}
            >
              {change.type}
            </span>

            {/* Severity Badge */}
            <span
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold rounded-lg border-2 uppercase",
                getSeverityColor(change.severity)
              )}
            >
              {getSeverityIcon(change.severity)}
              {change.severity}
            </span>

            {/* Business Impact Badge */}
            {change.severity === "critical" && (
              <span className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold bg-red-600 text-white rounded-lg shadow-lg animate-pulse">
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                USER IMPACT
              </span>
            )}
          </div>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-700 transition-all p-2 hover:bg-zinc-100 rounded-lg group"
            aria-label="Close (Press Esc)"
            title="Close (Press Esc)"
          >
            <X className="w-5 h-5 group-hover:scale-110 transition-transform" />
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="p-6 space-y-5">
        {/* Quick Actions with Toast Feedback */}
        <div className="pb-4 border-b border-zinc-200">
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyJSON}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-all hover:shadow-md"
              title="Copy change as JSON"
            >
              {copyStatus === 'json' ? (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span>Copy JSON</span>
                </>
              )}
            </button>
            <button
              onClick={handleExportMD}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-green-700 bg-green-50 hover:bg-green-100 border border-green-200 rounded-lg transition-all hover:shadow-md"
              title="Export to markdown"
            >
              {copyStatus === 'md' ? (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>Export MD</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Description */}
        <div>
          <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-2">
            Description
          </h4>
          <p className="text-sm text-zinc-800 leading-relaxed">
            {change.description}
          </p>
        </div>

        {/* AI Reasoning - Most Important Part */}
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
              <h4 className="text-xs font-bold text-blue-900 uppercase tracking-wide">
                AI Reasoning
              </h4>
            </div>
            {(() => {
              const hasContext = change.original_span.context_before && change.generated_span.context_before;
              const confidenceLevel = hasContext ? 'High' : 'Medium';
              const confidenceColor = hasContext ? 'blue' : 'yellow';
              return (
                <div className={`flex items-center gap-1.5 px-2 py-1 bg-${confidenceColor}-100 rounded-md`}>
                  <svg className={`w-3.5 h-3.5 text-${confidenceColor}-700`} fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  <span className={`text-xs font-bold text-${confidenceColor}-700`}>{confidenceLevel}</span>
                </div>
              );
            })()}
          </div>
          <p className="text-sm text-blue-900 font-medium leading-relaxed">
            {change.reasoning}
          </p>
        </div>

        {/* Text Comparison */}
        <div className="space-y-3">
          {/* Original */}
          <div className="bg-red-50 border-2 border-red-200 rounded-lg overflow-hidden">
            <div className="px-3 py-2 bg-red-100 border-b border-red-200">
              <span className="text-xs font-bold text-red-700 uppercase tracking-wide">
                Original Text
              </span>
            </div>
            <div className="max-h-28 overflow-y-auto scrollbar-thin scrollbar-thumb-red-300 scrollbar-track-red-50">
              <div className="text-sm text-red-900 bg-white p-3 leading-relaxed break-words">
                {change.original_span.context_before && (
                  <span className="text-red-600 opacity-60">
                    {change.original_span.context_before}
                  </span>
                )}
                <mark className="bg-red-200 text-red-900 font-extrabold px-1.5 py-0.5 rounded mx-0.5 border-2 border-red-300">
                  {change.original_span.text}
                </mark>
                {change.original_span.context_after && (
                  <span className="text-red-600 opacity-60">
                    {change.original_span.context_after}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Generated */}
          <div className="bg-green-50 border-2 border-green-200 rounded-lg overflow-hidden">
            <div className="px-3 py-2 bg-green-100 border-b border-green-200">
              <span className="text-xs font-bold text-green-700 uppercase tracking-wide">
                Generated Text
              </span>
            </div>
            <div className="max-h-28 overflow-y-auto scrollbar-thin scrollbar-thumb-green-300 scrollbar-track-green-50">
              <div className="text-sm text-green-900 bg-white p-3 leading-relaxed break-words">
                {change.generated_span.context_before && (
                  <span className="text-green-600 opacity-60">
                    {change.generated_span.context_before}
                  </span>
                )}
                <mark className="bg-green-200 text-green-900 font-extrabold px-1.5 py-0.5 rounded mx-0.5 border-2 border-green-300">
                  {change.generated_span.text}
                </mark>
                {change.generated_span.context_after && (
                  <span className="text-green-600 opacity-60">
                    {change.generated_span.context_after}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>


      </div>
    </div>
  );
}
