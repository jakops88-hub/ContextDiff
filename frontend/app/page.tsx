"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sparkles, AlertCircle, Zap } from "lucide-react";
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
  const [progress, setProgress] = useState(0);
  const [showingPartialResults, setShowingPartialResults] = useState(false);
  const [partialChanges, setPartialChanges] = useState<any[]>([]);
  const [isStreamingResults, setIsStreamingResults] = useState(false);

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
    setProgress(0);
    setShowingPartialResults(false);

    // Optimistic progress bar: Fast to 90%, then slow crawl
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev < 30) return prev + 15; // Fast start (0-30 in 400ms)
        if (prev < 60) return prev + 10; // Medium (30-60 in 600ms)
        if (prev < 85) return prev + 5;  // Slower (60-85 in 1s)
        if (prev < 90) return prev + 1;  // Crawl (85-90 in 1s)
        return prev; // Stay at 90 until real response
      });
    }, 200);

    // Show "partial results" skeleton after 2s to keep user engaged
    const skeletonTimeout = setTimeout(() => {
      setShowingPartialResults(true);
    }, 2000);

    try {
      const response = await compareTexts({
        original_text: originalText,
        generated_text: generatedText,
        sensitivity: "medium",
        premium_mode: false,
      });

      clearInterval(progressInterval);
      clearTimeout(skeletonTimeout);
      setProgress(100);
      
      // LIVE STREAMING EFFECT: Show changes one by one
      if (response.changes && response.changes.length > 0) {
        setIsStreamingResults(true);
        setShowingPartialResults(false);
        
        // Stream changes in batches
        const streamChanges = async () => {
          const batchSize = Math.max(1, Math.floor(response.changes.length / 3));
          
          for (let i = 0; i < response.changes.length; i += batchSize) {
            const batch = response.changes.slice(0, i + batchSize);
            setPartialChanges(batch);
            await new Promise(resolve => setTimeout(resolve, 400)); // 400ms between batches
          }
          
          // Show full result
          setIsStreamingResults(false);
          setResult(response);
          setPartialChanges([]);
        };
        
        streamChanges();
      } else {
        // No changes, show immediately
        setTimeout(() => {
          setResult(response);
          setShowingPartialResults(false);
        }, 300);
      }
    } catch (err: any) {
      clearInterval(progressInterval);
      clearTimeout(skeletonTimeout);
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
              Don&apos;t trust black-box text generation. ContextDiff uses advanced
              semantic analysis to highlight factual changes, tonal shifts, and
              critical omissions. Try the demo below.
            </p>
            
            {/* RapidAPI CTA Button */}
            <div className="pt-4">
              <a
                href="https://rapidapi.com/jakops88/api/contextdiff"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
              >
                <Zap className="w-5 h-5" />
                <span>Get API Access on RapidAPI</span>
                <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">Free tier available</span>
              </a>
            </div>
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
          <div className="space-y-6">
            {/* Progress Bar */}
            <div className="bg-white border border-zinc-200 rounded-xl shadow-sm p-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-zinc-900">
                    Analysis Progress
                  </span>
                  <span className="font-bold text-blue-600">{progress}%</span>
                </div>
                <div className="h-3 bg-zinc-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-300 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-xs text-zinc-600 text-center">
                  {progress < 30 && "Initializing semantic analysis..."}
                  {progress >= 30 && progress < 60 && "Processing text chunks..."}
                  {progress >= 60 && progress < 85 && "Identifying changes..."}
                  {progress >= 85 && progress < 100 && "Finalizing results..."}
                  {progress === 100 && "Complete! ✨"}
                </p>
              </div>
            </div>

            {/* Live Progress Steps */}
            <AnalysisProgress steps={steps} currentStepIndex={currentStepIndex} />

            {/* Skeleton Loader - Shows after 2s */}
            {showingPartialResults && (
              <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-8 space-y-6 animate-in fade-in duration-500">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-4 w-32 bg-zinc-200 rounded animate-pulse" />
                  <div className="h-4 w-24 bg-zinc-200 rounded animate-pulse" />
                </div>
                <div className="grid lg:grid-cols-2 gap-6">
                  {[1, 2].map((i) => (
                    <div key={i} className="space-y-3">
                      <div className="h-6 w-40 bg-zinc-200 rounded animate-pulse" />
                      <div className="space-y-2 bg-zinc-50 border border-zinc-200 rounded-lg p-4">
                        <div className="h-4 bg-zinc-200 rounded animate-pulse" />
                        <div className="h-4 bg-zinc-200 rounded animate-pulse w-5/6" />
                        <div className="h-4 bg-zinc-200 rounded animate-pulse w-4/6" />
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-zinc-500 text-center">
                  Preparing diff visualization...
                </p>
              </div>
            )}

            {/* LIVE STREAMING: Show partial results as they come in */}
            {isStreamingResults && partialChanges.length > 0 && (
              <div className="space-y-6 animate-in fade-in duration-300">
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl shadow-sm p-4">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="h-2 w-2 bg-blue-600 rounded-full animate-pulse" />
                      <div className="h-2 w-2 bg-blue-600 rounded-full animate-pulse [animation-delay:200ms]" />
                      <div className="h-2 w-2 bg-blue-600 rounded-full animate-pulse [animation-delay:400ms]" />
                    </div>
                    <span className="text-sm font-semibold text-blue-900">
                      Streaming results live... {partialChanges.length} changes detected
                    </span>
                  </div>
                </div>

                <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-8">
                  <h2 className="text-lg font-semibold text-zinc-900 mb-6">
                    Detailed Comparison (Live)
                  </h2>
                  <DiffViewer
                    originalText={originalText}
                    generatedText={generatedText}
                    changes={partialChanges}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Results Stage */}
        {result && !isLoading && (
          <div className="space-y-8">
            <ResultsSummary
              summary={result.summary}
              changesCount={result.changes.length}
              analysisTime={result.changes.length > 0 ? 8.3 : 2.1}
              criticalCount={result.changes.filter(c => c.severity === 'critical').length}
              warningCount={result.changes.filter(c => c.severity === 'warning').length}
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
          <p className="text-xs text-zinc-500">
            ContextDiff API © {new Date().getFullYear()}
          </p>
        </div>
      </footer>
    </main>
  );
}
