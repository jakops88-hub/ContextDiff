"use client";

import React from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import { AnalysisStep } from "@/hooks/useSimulatedProgress";
import { cn } from "@/lib/utils";

interface AnalysisProgressProps {
  steps: AnalysisStep[];
  currentStepIndex: number;
}

export default function AnalysisProgress({
  steps,
  currentStepIndex,
}: AnalysisProgressProps) {
  return (
    <div className="w-full max-w-2xl mx-auto space-y-4 py-8">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-zinc-900 mb-1">
          Analyzing Differences
        </h3>
        <p className="text-sm text-zinc-600">
          Deep semantic analysis in progress...
        </p>
      </div>

      <div className="bg-white border border-zinc-200 rounded-xl shadow-sm p-6 space-y-3">
        {steps.map((step, index) => {
          const isActive = index === currentStepIndex;
          const isCompleted = step.completed;
          const isUpcoming = index > currentStepIndex;

          return (
            <div
              key={step.id}
              className={cn(
                "flex items-center gap-3 p-3 rounded-lg transition-all duration-300",
                isActive && "bg-blue-50 border border-blue-200",
                isCompleted && "opacity-60"
              )}
            >
              <div className="flex-shrink-0">
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5 text-green-600 animate-in zoom-in duration-300" />
                ) : isActive ? (
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                ) : (
                  <div className="w-5 h-5 rounded-full border-2 border-zinc-300"></div>
                )}
              </div>
              <p
                className={cn(
                  "text-sm font-medium transition-colors",
                  isActive && "text-blue-900",
                  isCompleted && "text-zinc-600",
                  isUpcoming && "text-zinc-400"
                )}
              >
                {step.message}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
