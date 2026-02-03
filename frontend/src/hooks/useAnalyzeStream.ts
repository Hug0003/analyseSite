import { useState, useCallback } from "react";
import { AnalyzeResponse } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface StreamLog {
    type: "log";
    step: string;
    message: string;
}

interface StreamResult {
    type: "complete";
    data: AnalyzeResponse;
}

interface StreamError {
    type: "error";
    message: string;
}

type StreamMessage = StreamLog | StreamResult | StreamError;

interface UseAnalyzeStreamReturn {
    analyzeUrlStream: (url: string, lang?: string) => Promise<AnalyzeResponse>;
    logs: string[];
    currentStep: string | null;
}

export function useAnalyzeStream(): UseAnalyzeStreamReturn {
    const [logs, setLogs] = useState<string[]>([]);
    const [currentStep, setCurrentStep] = useState<string | null>(null);

    const analyzeUrlStream = useCallback(async (url: string, lang: string = "en"): Promise<AnalyzeResponse> => {
        setLogs([]);
        setCurrentStep("init");

        // Build Query URL
        const params = new URLSearchParams({ url, lang });
        const endpoint = `${API_BASE_URL}/api/stream?${params.toString()}`;

        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`Analyze failed: ${response.status} - ${errText}`);
            }

            if (!response.body) throw new Error("ReadableStream not supported by browser.");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let finalResult: AnalyzeResponse | null = null;
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");

                // Keep the last incomplete line in the buffer
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (!line.trim()) continue;

                    let msg: StreamMessage | null = null;
                    try {
                        msg = JSON.parse(line) as StreamMessage;
                    } catch (e) {
                        console.warn("Failed to parse stream line:", line, e);
                        continue;
                    }

                    if (msg) {
                        if (msg.type === "log") {
                            console.log(`[Stream] ${msg.step}: ${msg.message}`);
                            setLogs(prev => [...prev, msg.message]);
                            setCurrentStep(msg.step);
                        } else if (msg.type === "complete") {
                            finalResult = msg.data;
                        } else if (msg.type === "error") {
                            throw new Error(msg.message);
                        }
                    }
                }
            }

            if (!finalResult) throw new Error("Stream ended without result.");
            return finalResult;

        } catch (error) {
            console.error("Stream Error:", error);
            throw error;
        }
    }, []);

    return { analyzeUrlStream, logs, currentStep };
}
