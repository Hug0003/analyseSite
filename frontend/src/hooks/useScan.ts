
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { analyzeUrl } from "@/lib/api";
import { AnalyzeResponse } from "@/types";
import { useAuth } from "@/contexts/AuthContext";

// --- Hook for Analyzing URL (Mutation) ---
export function useAnalyze() {
    const queryClient = useQueryClient();
    const { isAuthenticated } = useAuth();

    // We can inject the logic to save to history here automatically on success! 
    // OR keep it in the UI component if it's too specific.
    // For now, let's keep it clean: simple wrapper around analyzeUrl.

    return useMutation({
        mutationFn: async ({ url, lang, competitorUrl }: { url: string, lang: string, competitorUrl?: string }) => {
            return await analyzeUrl(url, lang, competitorUrl);
        },
        onSuccess: () => {
            // If we had a list of scans query, we would invalidate it here
            if (isAuthenticated) {
                queryClient.invalidateQueries({ queryKey: ['history'] });
            }
        }
    });
}

// --- Hook for Saving History (Mutation) ---
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export function useSaveScan() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (scanData: AnalyzeResponse) => {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            const response = await fetch(`${API_BASE_URL}/api/audits/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    url: scanData.url,
                    score: scanData.global_score,
                    summary: {
                        seo: scanData.seo.scores.seo != null ? Math.round(scanData.seo.scores.seo <= 1 ? scanData.seo.scores.seo * 100 : scanData.seo.scores.seo) : 0,
                        security: Math.round(scanData.security.score),
                        performance: scanData.seo.scores.performance != null ? Math.round(scanData.seo.scores.performance <= 1 ? scanData.seo.scores.performance * 100 : scanData.seo.scores.performance) : 0
                    }
                })
            });

            if (!response.ok) throw new Error("Failed to save history");
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['history'] });
        }
    });
}

// --- Hook for Getting History (Query) ---
export function useHistory() {
    const { isAuthenticated } = useAuth();

    return useQuery({
        queryKey: ['history'],
        queryFn: async () => {
            const token = localStorage.getItem('access_token');
            if (!token) throw new Error("No token");

            const res = await fetch(`${API_BASE_URL}/api/audits/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Failed to fetch history");
            return res.json();
        },
        enabled: isAuthenticated, // Only run if logged in
    });
}
