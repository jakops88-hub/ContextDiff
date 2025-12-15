import { useState, useEffect } from "react";

export type AnalysisStep = {
  id: string;
  message: string;
  completed: boolean;
};

const ANALYSIS_STEPS: Omit<AnalysisStep, "completed">[] = [
  { id: "1", message: "Cleaning and normalizing text inputs..." },
  { id: "2", message: "Running initial equality check (Short-circuit)..." },
  { id: "3", message: "AI analyzing semantic structures..." },
  { id: "4", message: "Verifying factual consistency..." },
  { id: "5", message: "Finalizing response JSON..." },
];

export function useSimulatedProgress(isLoading: boolean) {
  const [steps, setSteps] = useState<AnalysisStep[]>(
    ANALYSIS_STEPS.map((step) => ({ ...step, completed: false }))
  );
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    if (!isLoading) {
      // Reset on new analysis
      setSteps(ANALYSIS_STEPS.map((step) => ({ ...step, completed: false })));
      setCurrentStepIndex(0);
      return;
    }

    // Simulate progress
    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => {
        const nextIndex = prev + 1;
        if (nextIndex < ANALYSIS_STEPS.length) {
          setSteps((prevSteps) =>
            prevSteps.map((step, idx) =>
              idx === prev ? { ...step, completed: true } : step
            )
          );
          return nextIndex;
        }
        return prev;
      });
    }, 800); // Faster intervals (800ms) for snappier UX

    return () => clearInterval(interval);
  }, [isLoading]);

  return { steps, currentStepIndex };
}
