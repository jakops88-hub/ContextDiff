"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sparkles, AlertCircle } from "lucide-react";
import { compareTexts, DiffResponse } from "@/lib/api";
import { useSimulatedProgress } from "@/hooks/useSimulatedProgress";
import AnalysisProgress from "@/components/AnalysisProgress";
import ResultsSummary from "@/components/ResultsSummary";
import DiffViewer from "@/components/DiffViewer";

const EXAMPLE_ORIGINAL = `Our product will be available in Q4 2024. The new features include advanced analytics, real-time collaboration, and enterprise-grade security. Pricing starts at $99 per month.`;

const EXAMPLE_GENERATED = `Our product might be available in Q4 2024. The new features include analytics, collaboration tools, and security features. Pricing information will be announced soon.`;

export default function Home() {
  const [originalText, setOriginalText] = useState("");
  const [generatedText, setGeneratedText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<DiffResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { steps, currentStepIndex } = useSimulatedProgress(isLoading);

  const handlePasteExample = () => {
    setOriginalText(EXAMPLE_ORIGINAL);
    setGeneratedText(EXAMPLE_GENERATED);
    setResult(null);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!originalText.trim() || !generatedText.trim()) {
      setError("Please enter both original and generated text.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await compareTexts({
        original_text: originalText,
        generated_text: generatedText,
        sensitivity: "medium",
        premium_mode: false,
      });

      setResult(response);
    } catch (err: any) {
      console.error("Analysis error:", err);
      setError(
        err.response?.data?.detail?.message ||
          err.message ||
          "Failed to analyze texts. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setOriginalText("");
    setGeneratedText("");
    setResult(null);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-zinc-50">
      {/* Hero Section */}
      <header className="bg-white border-b border-zinc-200">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="text-center space-y-4">
            <h1 className="text-5xl font-bold text-zinc-900 tracking-tight">
              Context<span className="text-blue-600">Diff</span>
            </h1>
            <p className="text-xl text-zinc-600 max-w-3xl mx-auto leading-relaxed">
              See What Your AI Actually Changed.
            </p>
            <p className="text-sm text-zinc-500 max-w-2xl mx-auto">
              Don't trust black-box text generation. ContextDiff uses advanced
              semantic analysis to highlight factual changes, tonal shifts, and
              critical omissions. Try the demo below.
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {!result && !isLoading && (
          <>
            {/* Input Stage */}
            <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-8 space-y-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-zinc-900">
                  Compare Your Texts
                </h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePasteExample}
                  className="text-blue-600"
                >
                  Paste Example
                </Button>
              </div>

              <div className="grid lg:grid-cols-2 gap-6">
                {/* Original Text */}
                <div className="space-y-3">
                  <label className="text-sm font-semibold text-zinc-700 uppercase tracking-wide">
                    Original Text (Source)
                  </label>
                  <textarea
                    value={originalText}
                    onChange={(e) => setOriginalText(e.target.value)}
                    placeholder="Paste your original text here..."
                    className="w-full h-64 px-4 py-3 text-sm border-2 border-zinc-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition-all resize-none font-mono"
                  />
                  <p className="text-xs text-zinc-500">
                    {originalText.length} characters
                  </p>
                </div>

                {/* Generated Text */}
                <div className="space-y-3">
                  <label className="text-sm font-semibold text-zinc-700 uppercase tracking-wide">
                    AI Generated Text (Candidate)
                  </label>
                  <textarea
                    value={generatedText}
                    onChange={(e) => setGeneratedText(e.target.value)}
                    placeholder="Paste the AI-generated version here..."
                    className="w-full h-64 px-4 py-3 text-sm border-2 border-zinc-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition-all resize-none font-mono"
                  />
                  <p className="text-xs text-zinc-500">
                    {generatedText.length} characters
                  </p>
                </div>
              </div>

              {/* CTA Button */}
              <div className="flex justify-center pt-4">
                <Button
                  size="lg"
                  onClick={handleAnalyze}
                  disabled={!originalText.trim() || !generatedText.trim()}
                  className="text-base"
                >
                  <Sparkles className="w-5 h-5" />
                  Analyze Differences
                </Button>
              </div>

              {/* Error Display */}
              {error && (
                <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg p-4">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-red-900">Error</p>
                    <p className="text-sm text-red-700 mt-1">{error}</p>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {/* Loading State */}
        {isLoading && (
          <AnalysisProgress steps={steps} currentStepIndex={currentStepIndex} />
        )}

        {/* Results Stage */}
        {result && !isLoading && (
          <div className="space-y-8">
            <ResultsSummary
              summary={result.summary}
              changesCount={result.changes.length}
            />

            <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-zinc-900">
                  Detailed Comparison
                </h2>
                <Button variant="outline" size="sm" onClick={handleReset}>
                  New Analysis
                </Button>
              </div>
              <DiffViewer
                originalText={originalText}
                generatedText={generatedText}
                changes={result.changes}
              />
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-zinc-200 mt-20">
        <div className="max-w-7xl mx-auto px-6 py-8 text-center text-sm text-zinc-600">
          <p>
            Built with ❤️ using Next.js, Tailwind CSS, and OpenAI GPT-4o-mini.
          </p>
          <p className="mt-2 text-xs text-zinc-500">
            ContextDiff API © {new Date().getFullYear()}
          </p>
        </div>
      </footer>
    </main>
  );
}
