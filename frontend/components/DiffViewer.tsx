"use client";

import React, { useState } from "react";
import { SemanticChange, TextSpan } from "@/lib/api";
import { cn } from "@/lib/utils";
import ChangeDetailCard from "./ChangeDetailCard";

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

  // Use context-aware matching with fallback strategies
  const matches: Array<{ start: number; end: number; change: SemanticChange }> = [];
  const usedRanges: Array<{ start: number; end: number }> = []; // Track used positions
  
  spans.forEach((span, spanIdx) => {
    if (!span.text || span.text.trim().length === 0) return;
    
    const searchText = span.text.trim();
    let foundStart = -1;
    
    // Strategy 1: Full context fingerprint (most reliable)
    if (span.context_before && span.context_after) {
      const before = span.context_before.trim();
      const after = span.context_after.trim();
      
      // Search for the complete pattern
      let searchPos = 0;
      while (searchPos < text.length) {
        const beforeIdx = text.indexOf(before, searchPos);
        if (beforeIdx === -1) break;
        
        const textStart = beforeIdx + before.length;
        const textEnd = textStart + searchText.length;
        const afterStart = textEnd;
        
        // Verify this is the correct match
        if (text.slice(textStart, textEnd) === searchText &&
            text.slice(afterStart, afterStart + after.length) === after) {
          
          // Check if this range overlaps with already used ranges
          const overlaps = usedRanges.some(used => 
            (textStart >= used.start && textStart < used.end) ||
            (textEnd > used.start && textEnd <= used.end) ||
            (textStart <= used.start && textEnd >= used.end)
          );
          
          if (!overlaps) {
            foundStart = textStart;
            break;
          }
        }
        
        searchPos = beforeIdx + 1;
      }
    }
    
    // Strategy 2: Before context only
    if (foundStart === -1 && span.context_before) {
      const before = span.context_before.trim();
      let searchPos = 0;
      
      while (searchPos < text.length) {
        const beforeIdx = text.indexOf(before, searchPos);
        if (beforeIdx === -1) break;
        
        const textStart = beforeIdx + before.length;
        const textEnd = textStart + searchText.length;
        
        if (text.slice(textStart, textEnd) === searchText) {
          const overlaps = usedRanges.some(used => 
            (textStart >= used.start && textStart < used.end) ||
            (textEnd > used.start && textEnd <= used.end)
          );
          
          if (!overlaps) {
            foundStart = textStart;
            break;
          }
        }
        
        searchPos = beforeIdx + 1;
      }
    }
    
    // Strategy 3: Direct text search (least reliable, last resort)
    if (foundStart === -1) {
      let searchPos = 0;
      while (searchPos < text.length) {
        const idx = text.indexOf(searchText, searchPos);
        if (idx === -1) break;
        
        const overlaps = usedRanges.some(used => 
          (idx >= used.start && idx < used.end) ||
          (idx + searchText.length > used.start && idx + searchText.length <= used.end)
        );
        
        if (!overlaps) {
          foundStart = idx;
          break;
        }
        
        searchPos = idx + 1;
      }
    }
    
    // Add match if found
    if (foundStart !== -1) {
      const matchEnd = foundStart + searchText.length;
      matches.push({
        start: foundStart,
        end: matchEnd,
        change: changes[spanIdx],
      });
      usedRanges.push({ start: foundStart, end: matchEnd });
    }
  });

  if (matches.length === 0) {
    return [{ text, isHighlight: false }];
  }

  // Sort by position and remove overlaps
  const sortedMatches = matches
    .sort((a, b) => a.start - b.start)
    .filter((match, idx, arr) => {
      if (idx === 0) return true;
      return match.start >= arr[idx - 1].end; // No overlap
    });

  let lastIndex = 0;

  sortedMatches.forEach(({ start, end, change }) => {
    // Add text before highlight
    if (start > lastIndex) {
      segments.push({
        text: text.slice(lastIndex, start),
        isHighlight: false,
      });
    }

    // Add highlighted text
    segments.push({
      text: text.slice(start, end),
      isHighlight: true,
      change,
    });

    lastIndex = end;
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
  selectedChangeId,
  onChangeClick,
}: {
  title: string;
  text: string;
  changes: SemanticChange[];
  isOriginal: boolean;
  selectedChangeId: string | null;
  onChangeClick: (change: SemanticChange) => void;
}) {
  const [hoveredChange, setHoveredChange] = useState<SemanticChange | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const segments = renderTextWithHighlights(text, changes, isOriginal);

  const handleMouseEnter = (change: SemanticChange, event: React.MouseEvent) => {
    setHoveredChange(change);
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    setTooltipPosition({
      x: rect.left + rect.width / 2,
      y: rect.bottom + 8,
    });
  };

  return (
    <div className="flex-1 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-700 uppercase tracking-wide">
          {title}
        </h3>
        <span className="text-xs text-zinc-500">{text.length} chars</span>
      </div>
      <div className="relative bg-white border border-zinc-200 rounded-lg p-6 shadow-sm min-h-[300px]">
        <div className="text-sm leading-relaxed text-zinc-800 break-words font-sans">
          {segments.map((segment, idx) => {
            if (!segment.isHighlight) {
              return <span key={idx}>{segment.text}</span>;
            }

            const isSelected = selectedChangeId === segment.change!.id;
            
            return (
              <span
                key={idx}
                className={cn(
                  "relative px-1 py-0.5 rounded border cursor-pointer transition-all",
                  getHighlightColor(segment.change!),
                  "hover:shadow-md",
                  isSelected && "ring-2 ring-blue-500 ring-offset-1 border-blue-400 shadow-lg"
                )}
                onMouseEnter={(e) => handleMouseEnter(segment.change!, e)}
                onMouseLeave={() => setHoveredChange(null)}
                onClick={() => onChangeClick(segment.change!)}
              >
                {segment.text}
              </span>
            );
          })}
        </div>

        {/* Tooltip */}
        {hoveredChange && (
          <div 
            className="fixed max-w-md p-4 bg-white border-2 border-zinc-300 rounded-lg shadow-2xl z-50 animate-in fade-in duration-150"
            style={{
              left: `${tooltipPosition.x}px`,
              top: `${tooltipPosition.y}px`,
              transform: 'translateX(-50%)',
            }}
          >
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
  const [selectedChangeId, setSelectedChangeId] = useState<string | null>(null);
  
  const selectedChange = selectedChangeId 
    ? changes.find(c => c.id === selectedChangeId) || null
    : null;

  const handleChangeClick = (change: SemanticChange) => {
    setSelectedChangeId(change.id === selectedChangeId ? null : change.id);
  };

  return (
    <div className="w-full space-y-6">
      {/* Layout: When inspector open, expand container width */}
      <div className={cn(
        "w-full transition-all duration-300",
        selectedChange ? "max-w-[95vw]" : "max-w-7xl"
      )}>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className={cn(
            "transition-all duration-300",
            selectedChange ? "lg:col-span-4" : "lg:col-span-6"
          )}>
            <TextColumn
              title="Original Text"
              text={originalText}
              changes={changes}
              isOriginal={true}
              selectedChangeId={selectedChangeId}
              onChangeClick={handleChangeClick}
            />
          </div>
          
          <div className={cn(
            "transition-all duration-300",
            selectedChange ? "lg:col-span-4" : "lg:col-span-6"
          )}>
            <TextColumn
              title="Generated Text"
              text={generatedText}
              changes={changes}
              isOriginal={false}
              selectedChangeId={selectedChangeId}
              onChangeClick={handleChangeClick}
            />
          </div>

          {/* Inspector Panel */}
          {selectedChange && (
            <div className="lg:col-span-4 animate-in slide-in-from-right duration-300">
              <div className="sticky top-6 max-h-[calc(100vh-3rem)] overflow-y-auto">
                <div className="mb-3">
                  <h3 className="text-sm font-semibold text-zinc-700 uppercase tracking-wide">
                    Insight Inspector
                  </h3>
                </div>
                <ChangeDetailCard 
                  change={selectedChange} 
                  onClose={() => setSelectedChangeId(null)}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Enhanced Legend & Stats */}
      <div className="bg-gradient-to-r from-zinc-50 to-white border border-zinc-200 rounded-lg p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4 text-xs">
            <span className="font-bold text-zinc-700 uppercase tracking-wide">Change Types:</span>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 bg-red-100 border border-red-300 rounded shadow-sm"></div>
              <span className="text-zinc-600 font-medium">Factual</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 bg-yellow-100 border border-yellow-300 rounded shadow-sm"></div>
              <span className="text-zinc-600 font-medium">Tone</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 bg-orange-100 border border-orange-300 rounded shadow-sm"></div>
              <span className="text-zinc-600 font-medium">Omission/Addition</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 bg-blue-100 border border-blue-300 rounded shadow-sm"></div>
              <span className="text-zinc-600 font-medium">Formatting</span>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <div className="px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-md">
              <span className="font-semibold text-blue-700">{changes.length}</span>
              <span className="text-blue-600 ml-1">changes detected</span>
            </div>
            <div className="px-3 py-1.5 bg-red-50 border border-red-200 rounded-md">
              <span className="font-semibold text-red-700">
                {changes.filter(c => c.severity === 'critical').length}
              </span>
              <span className="text-red-600 ml-1">critical</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
