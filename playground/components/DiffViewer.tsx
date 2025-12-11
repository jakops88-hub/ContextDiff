"use client";

import React, { useState } from "react";
import { SemanticChange, TextSpan } from "@/lib/api";
import { cn } from "@/lib/utils";

interface DiffViewerProps {
  originalText: string;
  generatedText: string;
  changes: SemanticChange[];
}

interface HighlightedSegment {
  text: string;
  isHighlight: boolean;
  change?: SemanticChange;
}

function getHighlightColor(change: SemanticChange): string {
  if (change.type === "FACTUAL" && change.severity === "critical") {
    return "bg-red-100 border-red-300 text-red-900";
  }
  if (change.type === "FACTUAL") {
    return "bg-red-50 border-red-200 text-red-800";
  }
  if (change.type === "TONE") {
    return "bg-yellow-50 border-yellow-200 text-yellow-900";
  }
  if (change.type === "CONTENT") {
    return "bg-orange-50 border-orange-200 text-orange-900";
  }
  return "bg-blue-50 border-blue-200 text-blue-900";
}

function renderTextWithHighlights(
  text: string,
  changes: SemanticChange[],
  isOriginal: boolean
): HighlightedSegment[] {
  if (changes.length === 0) {
    return [{ text, isHighlight: false }];
  }

  const segments: HighlightedSegment[] = [];
  const spans = changes.map((change) =>
    isOriginal ? change.original_span : change.generated_span
  );

  // Sort spans by start position
  const sortedSpans = [...spans]
    .map((span, idx) => ({ span, change: changes[idx] }))
    .sort((a, b) => a.span.start - b.span.start);

  let lastIndex = 0;

  sortedSpans.forEach(({ span, change }) => {
    // Add text before highlight
    if (span.start > lastIndex) {
      segments.push({
        text: text.slice(lastIndex, span.start),
        isHighlight: false,
      });
    }

    // Add highlighted text
    segments.push({
      text: text.slice(span.start, span.end),
      isHighlight: true,
      change,
    });

    lastIndex = span.end;
  });

  // Add remaining text
  if (lastIndex < text.length) {
    segments.push({
      text: text.slice(lastIndex),
      isHighlight: false,
    });
  }

  return segments;
}

function TextColumn({
  title,
  text,
  changes,
  isOriginal,
}: {
  title: string;
  text: string;
  changes: SemanticChange[];
  isOriginal: boolean;
}) {
  const [hoveredChange, setHoveredChange] = useState<SemanticChange | null>(null);
  const segments = renderTextWithHighlights(text, changes, isOriginal);

  return (
    <div className="flex-1 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-700 uppercase tracking-wide">
          {title}
        </h3>
        <span className="text-xs text-zinc-500">{text.length} chars</span>
      </div>
      <div className="relative bg-white border border-zinc-200 rounded-lg p-6 shadow-sm min-h-[300px]">
        <div className="text-sm leading-relaxed text-zinc-800 whitespace-pre-wrap font-mono">
          {segments.map((segment, idx) => {
            if (!segment.isHighlight) {
              return <span key={idx}>{segment.text}</span>;
            }

            return (
              <span
                key={idx}
                className={cn(
                  "relative px-1 py-0.5 rounded border cursor-help transition-all",
                  getHighlightColor(segment.change!),
                  "hover:shadow-md"
                )}
                onMouseEnter={() => setHoveredChange(segment.change!)}
                onMouseLeave={() => setHoveredChange(null)}
              >
                {segment.text}
              </span>
            );
          })}
        </div>

        {/* Tooltip */}
        {hoveredChange && (
          <div className="absolute top-full left-0 right-0 mt-2 p-4 bg-white border-2 border-zinc-200 rounded-lg shadow-xl z-10 animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "px-2 py-1 text-xs font-semibold rounded uppercase",
                    hoveredChange.type === "FACTUAL" && "bg-red-100 text-red-700",
                    hoveredChange.type === "TONE" && "bg-yellow-100 text-yellow-700",
                    hoveredChange.type === "CONTENT" && "bg-orange-100 text-orange-700",
                    hoveredChange.type === "FORMATTING" && "bg-blue-100 text-blue-700"
                  )}
                >
                  {hoveredChange.type}
                </span>
                <span
                  className={cn(
                    "px-2 py-1 text-xs font-medium rounded capitalize",
                    hoveredChange.severity === "critical" && "bg-red-600 text-white",
                    hoveredChange.severity === "warning" && "bg-yellow-600 text-white",
                    hoveredChange.severity === "info" && "bg-blue-600 text-white"
                  )}
                >
                  {hoveredChange.severity}
                </span>
              </div>
              <p className="text-sm font-medium text-zinc-900">
                {hoveredChange.description}
              </p>
              <p className="text-xs text-zinc-600 leading-relaxed">
                {hoveredChange.reasoning}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function DiffViewer({
  originalText,
  generatedText,
  changes,
}: DiffViewerProps) {
  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col lg:flex-row gap-6">
        <TextColumn
          title="Original Text"
          text={originalText}
          changes={changes}
          isOriginal={true}
        />
        <TextColumn
          title="Generated Text"
          text={generatedText}
          changes={changes}
          isOriginal={false}
        />
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-zinc-600 pt-4 border-t border-zinc-200">
        <span className="font-semibold">Legend:</span>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-red-100 border border-red-300 rounded"></div>
          <span>Factual</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-yellow-100 border border-yellow-300 rounded"></div>
          <span>Tone</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-orange-100 border border-orange-300 rounded"></div>
          <span>Content</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-blue-100 border border-blue-300 rounded"></div>
          <span>Formatting</span>
        </div>
      </div>
    </div>
  );
}
