"use client";

import { useState, useCallback, useEffect } from "react";
import { SearchBar } from "@/components/search-bar";
import { LoadingProgress } from "@/components/loading-progress";
import { Dashboard } from "@/components/dashboard";
import { AuthHeader } from "@/components/auth-header";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { analyzeUrl, healthCheck, ApiError } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";
import { AnalyzeResponse, AnalysisStep } from "@/types";
import { AlertCircle, Sparkles } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useAnalyzeStream } from "@/hooks/useAnalyzeStream";
import { useSaveScan } from "@/hooks/useScan";

type AppState = "idle" | "loading" | "results" | "error";

export default function Home() {
  const { t, language } = useLanguage();
  const { isAuthenticated } = useAuth();

  const [state, setState] = useState<AppState>("idle");
  const [steps, setSteps] = useState<AnalysisStep[]>([]);
  const [results, setResults] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isApiHealthy, setIsApiHealthy] = useState<boolean | null>(null);

  // Initialize steps with translations
  const getInitialSteps = useCallback((): AnalysisStep[] => [
    { id: "seo", label: t.steps.seo, status: "pending" },
    { id: "security", label: t.steps.security, status: "pending" },
    { id: "tech", label: t.steps.tech, status: "pending" },
    { id: "links", label: t.steps.links, status: "pending" },
  ], [t]);

  // Update steps when language changes
  useEffect(() => {
    if (state === "idle" || state === "error") {
      setSteps(getInitialSteps());
    }
  }, [t, state, getInitialSteps]);

  // Check API health on mount
  useEffect(() => {
    healthCheck().then(setIsApiHealthy);
  }, []);


  const { analyzeUrlStream, logs, currentStep } = useAnalyzeStream();
  const { mutate: mutateSaveScan } = useSaveScan();

  // Use logs to update step status visually
  useEffect(() => {
    if (state !== "loading" || !currentStep) return;

    setSteps(prev => prev.map(step => {
      // Map backend step names to frontend step IDs
      // backend: seo, security, tech, links
      // frontend ids: seo, security, tech, links
      if (step.id === currentStep) {
        return { ...step, status: "completed" };
      }
      return step;
    }));
  }, [currentStep, state]);

  const handleSearch = useCallback(async (url: string, competitorUrl?: string) => {
    setState("loading");
    setError(null);
    setSteps(getInitialSteps().map((s) => ({ ...s, status: "pending" })));

    try {
      // Use Streaming Hook
      const data = await analyzeUrlStream(url, language);

      // Save to history if authenticated
      if (isAuthenticated) {
        mutateSaveScan(data);
      }

      setSteps((prev) => prev.map((s) => ({ ...s, status: "completed" })));
      // Small delay just for UX smoothness
      await new Promise((resolve) => setTimeout(resolve, 500));

      setResults(data);
      setState("results");
    } catch (err: any) {
      console.error("Analysis error:", err);

      setSteps((prev) => prev.map(s => ({ ...s, status: "error" })));

      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err.message || t.home.apiUnavailable);
      }
      setState("error");
    }
  }, [getInitialSteps, t.home.apiUnavailable, language, isAuthenticated, analyzeUrlStream]);

  const handleBack = useCallback(() => {
    setState("idle");
    setResults(null);
    setError(null);
    setSteps(getInitialSteps());
  }, [getInitialSteps]);

  const handleRescan = useCallback(() => {
    if (results) {
      handleSearch(results.url);
    }
  }, [results, handleSearch]);

  // Show results dashboard
  if (state === "results" && results) {
    return <Dashboard data={results} onBack={handleBack} onRescan={handleRescan} />;
  }

  // Landing page with search
  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col">
      {/* Background effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-600/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-[128px]" />
      </div>

      {/* Header */}
      <AuthHeader />

      {/* Main content */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 pb-16">
        <div className="w-full max-w-3xl mx-auto text-center">
          {/* Hero text */}
          {state === "idle" && (
            <div className="mb-12 animate-fade-in">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 mb-6">
                <Sparkles className="w-4 h-4 text-violet-400" />
                <span className="text-sm text-violet-300">{t.home.badge}</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
                <span className="bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
                  {t.home.title1}
                </span>
                <br />
                <span className="bg-gradient-to-r from-violet-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  {t.home.title2}
                </span>
              </h1>

              <p className="text-lg text-zinc-400 max-w-xl mx-auto">
                {t.home.subtitle}
              </p>
            </div>
          )}

          {/* Loading title */}
          {state === "loading" && (
            <div className="mb-12">
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4">
                {t.home.analyzingTitle}
              </h2>
              <p className="text-zinc-400">
                {t.home.analyzingSubtitle}
              </p>
            </div>
          )}

          {/* Error title */}
          {state === "error" && (
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-red-400 mb-2">
                {t.home.analysisFailed}
              </h2>
            </div>
          )}

          {/* Search bar - show in idle or error state */}
          {(state === "idle" || state === "error") && (
            <>
              <SearchBar
                onSearch={handleSearch}
                isLoading={false}
                placeholder={t.home.placeholder}
                buttonText={t.common.analyze}
                helperText={t.home.helperText}
                className="mb-6"
              />

              {/* API Status */}
              {isApiHealthy === false && (
                <Alert variant="destructive" className="max-w-xl mx-auto mt-6 bg-red-500/10 border-red-500/30">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {t.home.apiUnavailable}
                  </AlertDescription>
                </Alert>
              )}

              {/* Error message */}
              {error && (
                <Alert variant="destructive" className="max-w-xl mx-auto mt-6 bg-red-500/10 border-red-500/30">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </>
          )}

          {/* Loading progress */}
          {state === "loading" && (
            <LoadingProgress steps={steps} logs={logs} className="mt-8" />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 py-6 text-center text-sm text-zinc-600">
        <p>{t.home.footer}</p>
      </footer>
    </div>
  );
}
